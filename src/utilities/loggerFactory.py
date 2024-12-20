from datetime import datetime
import logging
import os
from config import LOGS_FOLDER_PATH
from utilities.files import createFileIfNotExists
import re

MAX_LOG_FILES = 5          # Maximum amount of log files
MAX_LOG_BYTES = 1000000    # Maximum size of log file
LOGS_DATETIME_FORMAT = '%Y%m%d_%H%M%S'


def setup_task_logger(name: str, level: int):
    """Setup a new logger for the task."""
    def manage_old_logs():
        """Remove older logs if maximum amount exceeded."""
        log_files = sorted(
            [f for f in os.listdir(LOGS_FOLDER_PATH) if f.startswith("task_")],
            key=lambda x: os.path.getctime(os.path.join(LOGS_FOLDER_PATH, x))
        )

        while len(log_files) > MAX_LOG_FILES:
            oldest_log = log_files.pop(0)
            os.remove(os.path.join(LOGS_FOLDER_PATH, oldest_log))
            print(f"Log eliminado: {oldest_log}")

    # Name without spaces and extension
    formatted_name = re.sub(r"\s+", "_", name).split(".")[0]

    logger = logging.getLogger(f"task_{formatted_name}")
    logger.setLevel(level)

    # Create a new log file for each task
    log_file = os.path.join(
        LOGS_FOLDER_PATH,
        f"task_{formatted_name}_{datetime.now().strftime(LOGS_DATETIME_FORMAT)}.log"
    )
    file_handler = logging.FileHandler(log_file, "w", delay=True)

    # Log format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    manage_old_logs()
    logger.addHandler(file_handler)

    return logger


def setup_stream_logger(name: str, level: int):
    """Setup a new logger for the stream."""
    logger = logging.getLogger(f"task_{name}")
    logger.setLevel(level)

    # Configure the file to save logs
    log_file = os.path.join(
        LOGS_FOLDER_PATH,
        f"{name}.log"
    )
    createFileIfNotExists(log_file)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        mode="a",
        maxBytes=MAX_LOG_BYTES,
        backupCount=MAX_LOG_FILES
    )

    # Log format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger
