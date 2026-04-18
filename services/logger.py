import logging
from datetime import datetime

import pytz

from config.settings import LOG_FILE, TIMEZONE


class TimezoneFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, timezone_name=TIMEZONE):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.timezone = pytz.timezone(timezone_name)

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, self.timezone)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]


def setup_logger():
    logger = logging.getLogger("web_automation")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_format = "%(asctime)s IST [%(levelname)s] %(message)s"

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(TimezoneFormatter(log_format))
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(TimezoneFormatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()
