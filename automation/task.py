import time

from playwright.sync_api import sync_playwright

from config.settings import MAX_RETRIES, RETRY_DELAY
from services.logger import logger
from services.mailer import send_alert_email, send_success_email

from .actions import perform_attendance_action
from .login import login_to_portal

CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--no-first-run",
    "--no-zygote",
]


def _safe_close(resource, name):
    if resource is None:
        return
    try:
        resource.close()
    except Exception as exc:
        logger.warning("Could not close %s cleanly: %s", name, exc)


def _read_recent_logs():
    try:
        with open("logs/app.log", "r", encoding="utf-8") as file_obj:
            return "".join(file_obj.readlines()[-20:])
    except Exception:
        return "Could not retrieve logs."


def run_attendance_task():
    attempt = 0

    while attempt < MAX_RETRIES:
        attempt += 1
        logger.info("Starting attendance task (Attempt %s/%s)", attempt, MAX_RETRIES)

        browser = None
        context = None
        page = None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=CHROMIUM_ARGS,
                    chromium_sandbox=False,
                )

                context = browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    java_script_enabled=True,
                    ignore_https_errors=True,
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )

                page = context.new_page()
                try:
                    login_to_portal(page)
                    action_name = perform_attendance_action(page)

                    logger.info("Attendance task completed successfully.")
                    send_success_email(action_name)
                    return True
                finally:
                    _safe_close(page, "page")
                    _safe_close(context, "browser context")
                    _safe_close(browser, "browser")
                    page = None
                    context = None
                    browser = None

        except Exception as exc:
            logger.error("Task failed on attempt %s: %s", attempt, exc)

            if attempt < MAX_RETRIES:
                logger.info("Retrying in %ss...", RETRY_DELAY)
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Max retries reached. Sending alert.")
                send_alert_email(str(exc), _read_recent_logs(), attempts=attempt)
                return False
