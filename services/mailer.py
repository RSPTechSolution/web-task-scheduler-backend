import html
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz

from config.settings import ALERT_EMAIL, SMTP_PASS, SMTP_PORT, SMTP_SERVER, SMTP_USER, TIMEZONE
from services.logger import logger


def _current_timestamp_strings():
    timezone = pytz.timezone(TIMEZONE)
    now = datetime.now(timezone)
    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %I:%M:%S %p %Z")


def _send_email(subject, html_body, success_log_message, failure_log_message):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = ALERT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info("%s to %s", success_log_message, ALERT_EMAIL)
    except Exception as exc:
        logger.error("%s: %s", failure_log_message, exc)


def send_alert_email(error_message, logs_snapshot="", attempts=0):
    current_date, current_time = _current_timestamp_strings()
    subject = f"⚠️ Attendance Failed - Action Required ({current_date})"
    html_body = f"""
<h2 style="color:#c62828; margin-bottom:10px;">
  Attendance Task Failed
</h2>

<p style="color:#333;">
  The automated attendance process could not complete successfully after multiple attempts.
</p>

<table style="width:100%; margin-top:15px; border-collapse:collapse;">
  <tr>
    <td style="padding:8px; font-weight:bold;">Time</td>
    <td style="padding:8px;">{html.escape(current_time)}</td>
  </tr>
  <tr style="background:#f9f9f9;">
    <td style="padding:8px; font-weight:bold;">Attempts</td>
    <td style="padding:8px;">{attempts}</td>
  </tr>
  <tr>
    <td style="padding:8px; font-weight:bold;">Status</td>
    <td style="padding:8px; color:#c62828;">Failed</td>
  </tr>
</table>

<h3 style="margin-top:20px; color:#333;">Error Details</h3>
<div style="background:#fff3f3; border:1px solid #ffcdd2; padding:10px; border-radius:5px; color:#c62828;">
  {html.escape(error_message)}
</div>

<h3 style="margin-top:20px; color:#333;">Recent Logs</h3>
<pre style="background:#f5f5f5; padding:10px; border-radius:5px; font-size:12px; overflow:auto;">{html.escape(logs_snapshot)}</pre>

<p style="margin-top:20px; color:#777; font-size:12px;">
  Please review the issue or check the automation system dashboard.
</p>
"""
    _send_email(
        subject,
        html_body,
        "Alert email sent",
        "Failed to send alert email",
    )


def send_success_email(action):
    current_date, current_time = _current_timestamp_strings()
    subject = f"✔️ Attendance Success - {action} Completed ({current_date})"
    html_body = f"""
<h2 style="color:#2e7d32; margin-bottom:10px;">
  Attendance {html.escape(action)} Successful
</h2>

<p style="color:#333;">
  Your attendance action was completed successfully.
</p>

<table style="width:100%; margin-top:15px; border-collapse:collapse;">
  <tr>
    <td style="padding:8px; font-weight:bold;">Action</td>
    <td style="padding:8px;">{html.escape(action)}</td>
  </tr>
  <tr style="background:#f9f9f9;">
    <td style="padding:8px; font-weight:bold;">Time</td>
    <td style="padding:8px;">{html.escape(current_time)}</td>
  </tr>
  <tr>
    <td style="padding:8px; font-weight:bold;">Status</td>
    <td style="padding:8px; color:#2e7d32;">Success</td>
  </tr>
</table>

<p style="margin-top:20px; color:#777; font-size:12px;">
  This is an automated notification from your Web Automation System.
</p>
"""
    _send_email(
        subject,
        html_body,
        "Success email sent",
        "Failed to send success email",
    )


def send_skipped_email(action):
    current_date, current_time = _current_timestamp_strings()
    subject = f"ℹ️ Attendance Skipped - {action} (Already Done) ({current_date})"
    html_body = f"""
<h2 style="color:#1976d2; margin-bottom:10px;">
  Attendance Action Skipped
</h2>

<p style="color:#333;">
  The scheduled <strong>{html.escape(action)}</strong> task was skipped because the system detected that you are already in the requested state.
</p>

<table style="width:100%; margin-top:15px; border-collapse:collapse;">
  <tr>
    <td style="padding:8px; font-weight:bold;">Attempted Action</td>
    <td style="padding:8px;">{html.escape(action)}</td>
  </tr>
  <tr style="background:#f9f9f9;">
    <td style="padding:8px; font-weight:bold;">Time</td>
    <td style="padding:8px;">{html.escape(current_time)}</td>
  </tr>
  <tr>
    <td style="padding:8px; font-weight:bold;">Result</td>
    <td style="padding:8px; color:#1976d2;">Already Event Found - No Action Needed</td>
  </tr>
</table>

<p style="margin-top:20px; color:#777; font-size:12px;">
  This is an automated notification from your Web Automation System.
</p>
"""
    _send_email(
        subject,
        html_body,
        "Skip email sent",
        "Failed to send skip email",
    )
