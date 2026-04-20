import os

from dotenv import load_dotenv

load_dotenv()

# Portal Config
USERNAME = os.getenv("PORTAL_USERNAME")
PASSWORD = os.getenv("PORTAL_PASSWORD")
LOGIN_URL = os.getenv("LOGIN_URL")
HOME_URL = os.getenv("HOME_URL")

# Email Config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Dashboard Auth
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "change-me")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "replace-this-secret-key")
FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173,http://127.0.0.1:5173",
)
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
FRONTEND_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGIN.split(",") if origin.strip()]

# App Config
LOG_FILE = "logs/app.log"
SCHEDULER_STATE_FILE = "data/scheduler_state.json"
TIMEZONE = "Asia/Kolkata"
SIGNIN_TIME = os.getenv("SIGNIN_TIME", "10:20")
SIGNOUT_TIME = os.getenv("SIGNOUT_TIME", "21:00")
MAX_RETRIES = 3
RETRY_DELAY = 10
