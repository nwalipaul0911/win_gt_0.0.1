import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Optional, Any
# === Formatter ===
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - line %(lineno)d - %(message)s"
)

error_formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - line %(lineno)d - %(message)s"
)

# === Helper to create daily rotating log handlers in subfolders ===
def get_daily_handler(category: str, level: str| int=logging.INFO, formatter: Optional[logging.Formatter]=None) -> TimedRotatingFileHandler:
    """Returns a daily rotating handler writing logs to logs/<category>/<category>-YYYY-MM-DD.log"""
    log_dir = os.path.join("logs", category)
    os.makedirs(log_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(log_dir, f"{category}-{date_str}.log")

    handler = TimedRotatingFileHandler(
        file_path, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    handler.suffix = "%Y-%m-%d"
    return handler

# === Session Logger ===
session_logger = logging.getLogger("gazetime.session")
session_logger.setLevel(logging.INFO)
session_logger.addHandler(get_daily_handler("session", level=logging.INFO, formatter=formatter))
session_logger.propagate = False  # Prevent double logging in root

# === Error Logger (for exceptions) ===
error_handler = get_daily_handler("error", level=logging.ERROR, formatter=error_formatter)

# === App Logger (general app activity) ===
app_handler = get_daily_handler("app", level=logging.INFO, formatter=formatter)

# === Root Logger ===
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(app_handler)
root_logger.addHandler(error_handler)
