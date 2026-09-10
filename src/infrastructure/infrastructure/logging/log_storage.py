from pathlib import Path
from typing import IO

from core.config import LOGS_FOLDER_PATH
from core.ports.log_storage import ILogStorage
from core.utilities.files import getFilesInFolder


class LogStorage(ILogStorage):
    """Concrete ILogStorage implementation using the local filesystem."""

    def get_log_path(self, file_name: str) -> Path:
        """Return the absolute path for a log file name."""
        return Path(LOGS_FOLDER_PATH) / file_name

    def log_exists(self, file_name: str) -> bool:
        """Return True if a log file with *file_name* exists in storage."""
        return self.get_log_path(file_name).exists()

    def get_all_log_paths(self) -> list[str]:
        """Return a list of all log file names."""
        return getFilesInFolder(LOGS_FOLDER_PATH)

    def open_for_reading(self, filename: str) -> IO[str]:
        """Open *filename* for sequential text reading and return the stream object."""
        log_path = self.get_log_path(filename)
        return open(log_path, "r")
