import re
import threading
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from automation.task import run_attendance_task
from config.settings import (
    DASHBOARD_PASSWORD,
    FLASK_SECRET_KEY,
    FRONTEND_ORIGINS,
    LOG_FILE,
    SESSION_COOKIE_SECURE,
)
from scheduler import (
    block_date,
    get_scheduler_snapshot,
    pause_scheduler,
    resume_scheduler,
    unblock_date,
)
from services.logger import logger

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None" if SESSION_COOKIE_SECURE else "Lax",
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
)

CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": FRONTEND_ORIGINS}},
)

LOG_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
    r"(?P<timezone>[A-Z]+) "
    r"\[(?P<level>[A-Z]+)\] (?P<message>.*)$"
)


def api_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "Authentication required."}), 401
        return view_func(*args, **kwargs)

    return wrapped_view


def _load_log_entries(limit=120):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as file_obj:
            lines = file_obj.readlines()
    except OSError as exc:
        return [
            {
                "timestamp": "",
                "timezone": "IST",
                "level": "ERROR",
                "message": f"Could not load logs: {exc}",
            }
        ]

    entries = []
    current_entry = None

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        match = LOG_LINE_PATTERN.match(line)
        if match:
            if current_entry:
                entries.append(current_entry)
            current_entry = match.groupdict()
        elif current_entry and line.strip():
            current_entry["message"] += f"\n{line}"

    if current_entry:
        entries.append(current_entry)

    recent_entries = entries[-limit:]
    for entry in recent_entries:
        entry["human"] = (
            f"{entry['timestamp']} {entry.get('timezone', 'IST')}  "
            f"{entry['level'].title()}  {entry['message']}"
        )

    return recent_entries


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/auth/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    password = payload.get("password", "")
    if password != DASHBOARD_PASSWORD:
        logger.warning("Dashboard login failed.")
        return jsonify({"error": "Incorrect password."}), 401

    session["authenticated"] = True
    session.permanent = True
    logger.info("Dashboard login successful.")
    return jsonify({"ok": True, "authenticated": True})


@app.route("/api/auth/logout", methods=["POST"])
@api_login_required
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/session", methods=["GET"])
def session_status():
    return jsonify({"authenticated": bool(session.get("authenticated"))})


@app.route("/api/dashboard", methods=["GET"])
@api_login_required
def dashboard_data():
    return jsonify(get_scheduler_snapshot())


@app.route("/api/logs", methods=["GET"])
@api_login_required
def get_logs():
    return jsonify({"entries": _load_log_entries()})


@app.route("/api/run", methods=["POST"])
@api_login_required
def trigger_run():
    logger.info("Manual trigger initiated via dashboard")
    threading.Thread(target=run_attendance_task, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/pause", methods=["POST"])
@api_login_required
def toggle_pause():
    snapshot = get_scheduler_snapshot()
    if snapshot["paused"]:
        resume_scheduler()
    else:
        pause_scheduler()
    return jsonify(get_scheduler_snapshot())


@app.route("/api/blocked-dates", methods=["POST"])
@api_login_required
def add_blocked_date():
    payload = request.get_json(silent=True) or {}
    date_string = payload.get("date", "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string):
        return jsonify({"error": "Date must be in YYYY-MM-DD format."}), 400

    block_date(date_string)
    return jsonify(get_scheduler_snapshot())


@app.route("/api/blocked-dates/<date_string>", methods=["DELETE"])
@api_login_required
def remove_blocked_date(date_string):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string):
        return jsonify({"error": "Date must be in YYYY-MM-DD format."}), 400

    unblock_date(date_string)
    return jsonify(get_scheduler_snapshot())
