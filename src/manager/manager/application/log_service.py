"""Application service for log file operations."""

from pathlib import Path

from core.ports.log_storage import ILogStorage

from manager.application.log_manager import LogManager


class LogService:
    """Encapsulates log storage operations for API consumers."""

    def __init__(self, storage: ILogStorage):
        self._manager = LogManager(storage)

    def classify_log_files(self) -> list[dict]:
        return self._manager.classify_log_files()

    def get_log_path(self, log_name: str) -> Path:
        return self._manager.get_log_path(log_name)

    def log_exists(self, log_name: str) -> bool:
        return self._manager.log_exists(log_name)

    def generate_log_csv(self, log_name: str) -> str:
        return self._manager.generate_log_csv(log_name)
