"""ILogStorage port — the minimal interface for a log storage backend."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Protocol, runtime_checkable


@runtime_checkable
class ILogStorage(Protocol):
    """Structural interface for a log storage backend."""

    def get_log_path(self, user_id: int, filename: str) -> Path:
        """Return the absolute path to a user's log file (does not check existence)."""
        ...

    def log_exists(self, filename: str) -> bool:
        """Return True if a log file with *filename* exists in storage."""
        ...

    def get_all_log_paths(self) -> list[Path]:
        """Return a list of all log file names."""
        ...

    def open_for_reading(self, filename: str) -> IO[str]:
        """Open *filename* for sequential text reading and return the stream object."""
        ...
