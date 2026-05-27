"""IFileStorage port — the minimal filesystem interface."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Protocol, runtime_checkable


@runtime_checkable
class IFileStorage(Protocol):
    """Structural interface for a user-scoped file storage backend."""

    def get_file_path(self, user_id: int, filename: str) -> Path:
        """Return the absolute path to a user's file (does not check existence)."""
        ...

    def read_file(self, user_id: int, filename: str) -> str:
        """Return the text content of a user's file."""
        ...

    def save_file(self, user_id: int, file: IO, filename: str) -> Path:
        """Persist *file* under the user's directory and return the final path."""
        ...

    def copy_file(self, user_id: int, original_path: str, filename: str) -> Path:
        """Copy an existing file into the user's directory and return the final path."""
        ...

    def rename_file(self, user_id: int, filename: str, new_filename: str) -> Path:
        """Rename a file inside the user's directory and return the new path."""
        ...

    def delete_file(self, user_id: int, filename: str) -> None:
        """Delete a file from the user's directory."""
        ...

    def open_for_reading(self, path: str | Path) -> IO[str]:
        """Open *path* for sequential text reading and return the file object."""
        ...
