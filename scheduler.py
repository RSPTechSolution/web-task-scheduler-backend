import json
import os
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from automation.task import run_attendance_task
from config.settings import (
    SCHEDULER_STATE_FILE,
    SIGNIN_TIME,
    SIGNOUT_TIME,
    TIMEZONE,
)
from services.logger import logger

scheduler = BackgroundScheduler(timezone=TIMEZONE)
is_paused = False


def _ensure_state_dir():
    state_dir = os.path.dirname(SCHEDULER_STATE_FILE)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)


def _default_state():
    return {"blocked_dates": []}


def _read_state():
    _ensure_state_dir()
    if not os.path.exists(SCHEDULER_STATE_FILE):
        return _default_state()

    try:
        with open(SCHEDULER_STATE_FILE, "r", encoding="utf-8") as file_obj:
            state = json.load(file_obj)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read scheduler state file cleanly: %s", exc)
        return _default_state()

    state.setdefault("blocked_dates", [])
    return state


def _write_state(state):
    _ensure_state_dir()
    with open(SCHEDULER_STATE_FILE, "w", encoding="utf-8") as file_obj:
        json.dump(state, file_obj, indent=2, sort_keys=True)


def _today_string():
    timezone = pytz.timezone(TIMEZONE)
    return datetime.now(timezone).strftime("%Y-%m-%d")


def get_blocked_dates():
    state = _read_state()
    return sorted(set(state.get("blocked_dates", [])))


def block_date(date_string):
    state = _read_state()
    blocked_dates = set(state.get("blocked_dates", []))
    blocked_dates.add(date_string)
    state["blocked_dates"] = sorted(blocked_dates)
    _write_state(state)
    logger.info("Scheduler blocked for date %s", date_string)


def unblock_date(date_string):
    state = _read_state()
    blocked_dates = set(state.get("blocked_dates", []))
    if date_string in blocked_dates:
        blocked_dates.remove(date_string)
        state["blocked_dates"] = sorted(blocked_dates)
        _write_state(state)
        logger.info("Scheduler unblocked for date %s", date_string)


def is_date_blocked(date_string=None):
    check_date = date_string or _today_string()
    return check_date in set(get_blocked_dates())


def should_run_today():
    if is_paused:
        logger.info("Scheduled run skipped because scheduler is paused globally.")
        return False

    if is_date_blocked():
        logger.info("Scheduled run skipped because today is blocked in the dashboard calendar.")
        return False

    return True


def run_scheduled_attendance(job_name):
    if not should_run_today():
        logger.info("Skipping job '%s' for today.", job_name)
        return False

    logger.info("Running scheduled job '%s'", job_name)
    return run_attendance_task(target_action=job_name)


def start_scheduler():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started.")

    # Parse times from .env
    try:
        in_h, in_m = map(int, SIGNIN_TIME.split(':'))
        out_h, out_m = map(int, SIGNOUT_TIME.split(':'))
    except Exception as e:
        logger.error(f"Failed to parse scheduler times from .env: {e}. Falling back to defaults.")
        in_h, in_m = 10, 20
        out_h, out_m = 21, 0

    # Check and add Sign-in job if it doesn't exist
    if not scheduler.get_job("attendance_signin"):
        scheduler.add_job(
            run_scheduled_attendance,
            CronTrigger(day_of_week="mon-fri", hour=in_h, minute=in_m, timezone=TIMEZONE),
            args=["Sign-in"],
            id="attendance_signin",
            name="Sign-in",
            replace_existing=True,
        )
        logger.info(f"Added 'Sign-in' job (Mon-Fri {in_h:02d}:{in_m:02d} IST)")

    # Check and add Sign-out job if it doesn't exist
    if not scheduler.get_job("attendance_signout"):
        scheduler.add_job(
            run_scheduled_attendance,
            CronTrigger(day_of_week="mon-fri", hour=out_h, minute=out_m, timezone=TIMEZONE),
            args=["Sign-out"],
            id="attendance_signout",
            name="Sign-out",
            replace_existing=True,
        )
        logger.info(f"Added 'Sign-out' job (Mon-Fri {out_h:02d}:{out_m:02d} IST)")

    logger.info("Scheduler check complete.")


def pause_scheduler():
    global is_paused
    is_paused = True
    scheduler.pause()
    logger.info("Scheduler paused")


def resume_scheduler():
    global is_paused
    is_paused = False
    scheduler.resume()
    logger.info("Scheduler resumed")


def get_next_runs():
    timezone = pytz.timezone(TIMEZONE)
    runs = []

    for job in scheduler.get_jobs():
        next_run = job.next_run_time.astimezone(timezone) if job.next_run_time else None
        runs.append(
            {
                "job_id": job.id,
                "name": job.name,
                "next_run": next_run.strftime("%Y-%m-%d %I:%M:%S %p %Z") if next_run else "N/A",
            }
        )

    return runs


def get_scheduler_snapshot():
    timezone = pytz.timezone(TIMEZONE)
    now = datetime.now(timezone)
    return {
        "paused": is_paused,
        "timezone": TIMEZONE,
        "blocked_dates": get_blocked_dates(),
        "today": now.strftime("%Y-%m-%d"),
        "now": now.strftime("%Y-%m-%d %I:%M:%S %p %Z"),
        "next_runs": get_next_runs(),
    }
