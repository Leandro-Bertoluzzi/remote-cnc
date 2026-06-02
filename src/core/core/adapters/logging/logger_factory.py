"""Infrastructure logger factories.

These functions create ``logging.Logger`` instances backed by filesystem
handlers. ``logging.Logger`` satisfies the ``ILogger`` protocol structurally,
so no explicit casting is needed.
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime

from core.config import LOGS_DATETIME_FORMAT, LOGS_FOLDER_PATH
from core.utilities.files import createFileIfNotExists

MAX_LOG_FILES = 5  # Maximum number of task log files to keep
MAX_LOG_BYTES = 1_000_000  # Maximum size of a rotating log file (bytes)

_LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
_DATE_FORMAT = "%d/%m/%Y %H:%M:%S"


def setup_task_logger(name: str, level: int) -> logging.Logger:
    """Create a per-task file logger.

    A new log file is created on every call:
    ``task_{name}_{YYYYMMDD_hhmmss}.log`` under ``LOGS_FOLDER_PATH``.
    Older task log files are removed once the total exceeds ``MAX_LOG_FILES``.

    Args:
        name: Human-readable name (typically the G-code filename).
              Spaces are replaced by underscores; file extensions are stripped.
        level: Logging level (e.g. ``logging.INFO``).

    Returns:
        A configured ``logging.Logger`` instance.
    """

    def _manage_old_logs() -> None:
        log_files = sorted(
            [f for f in os.listdir(LOGS_FOLDER_PATH) if f.startswith("task_")],
            key=lambda x: os.path.getctime(os.path.join(LOGS_FOLDER_PATH, x)),
        )
        while len(log_files) > MAX_LOG_FILES:
            oldest = log_files.pop(0)
            os.remove(os.path.join(LOGS_FOLDER_PATH, oldest))

    # Sanitise: replace whitespace with underscores, strip extension
    formatted_name = re.sub(r"\s+", "_", name).split(".")[0]

    logger = logging.getLogger(f"task_{formatted_name}")
    logger.setLevel(level)

    log_file = os.path.join(
        LOGS_FOLDER_PATH,
        f"task_{formatted_name}_{datetime.now().strftime(LOGS_DATETIME_FORMAT)}.log",
    )
    file_handler = logging.FileHandler(log_file, mode="w", delay=True)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    _manage_old_logs()
    logger.addHandler(file_handler)

    return logger


def setup_stream_logger(name: str, level: int) -> logging.Logger:
    """Create a rotating file logger for long-running streams.

    Logs are appended to ``{name}.log`` under ``LOGS_FOLDER_PATH`` and
    rotated automatically when the file reaches ``MAX_LOG_BYTES``.

    Args:
        name: Logger/file name (e.g. ``"gateway"``, ``"controller"``).
        level: Logging level (e.g. ``logging.INFO``).

    Returns:
        A configured ``logging.Logger`` instance.
    """
    logger = logging.getLogger(f"task_{name}")
    logger.setLevel(level)

    log_file = os.path.join(LOGS_FOLDER_PATH, f"{name}.log")
    createFileIfNotExists(log_file)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        mode="a",
        maxBytes=MAX_LOG_BYTES,
        backupCount=MAX_LOG_FILES,
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    logger.addHandler(file_handler)

    return logger
