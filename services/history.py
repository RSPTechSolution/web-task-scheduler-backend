import json
import os
from datetime import datetime
import pytz
from config.settings import TIMEZONE

HISTORY_FILE = "data/history.json"

def _ensure_data_dir():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

def _read_history():
    _ensure_data_dir()
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _write_history(history):
    _ensure_data_dir()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def add_history_entry(job_name, status, message):
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    entry = {
        "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p %Z"),
        "job_name": job_name,
        "status": status, # 'Success', 'Skipped', 'Failed'
        "message": message
    }
    
    history = _read_history()
    history.insert(0, entry) # Add to beginning
    history = history[:50] # Keep last 50
    _write_history(history)

def get_history():
    return _read_history()
