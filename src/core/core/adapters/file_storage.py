"""FileSystemStorage — concrete IFileStorage adapter backed by the local filesystem."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import IO

from core.utilities.files import ALLOWED_FILE_EXTENSIONS, FileSystemError, InvalidFile


class FileSystemStorage:
    """Stores user files in a base directory structured as ``<base>/<user_id>/<filename>``."""

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_filename(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

    def _user_folder(self, user_id: int) -> Path:
        """Return the path to the user's folder, creating it if necessary."""
        folder = self.base_path / str(user_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    # ------------------------------------------------------------------
    # IFileStorage implementation
    # ------------------------------------------------------------------

    def get_file_path(self, user_id: int, filename: str) -> Path:
        """Return the absolute path to a user's file (does not check existence)."""
        return self.base_path / str(user_id) / filename

    def read_file(self, user_id: int, filename: str) -> str:
        """Return the text content of a user's file."""
        file_path = self.get_file_path(user_id, filename)
        try:
            with open(file_path, "r") as content:
                return content.read()
        except Exception as error:
            raise FileSystemError(f"There was an error reading the file: {error}") from error

    def save_file(self, user_id: int, file: IO, filename: str) -> Path:
        """Persist *file* under the user's directory and return the final path."""
        if not self._is_valid_filename(filename):
            raise InvalidFile(f"Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}")

        destination = self._user_folder(user_id) / filename
        try:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file, buffer)
        except Exception as error:
            raise FileSystemError(
                f"There was an error writing the file in the file system: {error}"
            ) from error

        return destination

    def copy_file(self, user_id: int, original_path: str, filename: str) -> Path:
        """Copy an existing file into the user's directory and return the final path."""
        if not self._is_valid_filename(filename):
            raise InvalidFile(f"Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}")

        destination = self._user_folder(user_id) / filename
        try:
            shutil.copy(original_path, destination)
        except Exception as error:
            raise FileSystemError(
                f"There was an error writing the file in the file system: {error}"
            ) from error

        return destination

    def rename_file(self, user_id: int, filename: str, new_filename: str) -> Path:
        """Rename a file inside the user's directory and return the new path."""
        if not self._is_valid_filename(new_filename):
            raise InvalidFile(f"Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}")

        user_folder = self._user_folder(user_id)
        try:
            current_file_path = user_folder / filename
            new_file_path = user_folder / new_filename
            current_file_path.rename(new_file_path)
        except Exception as error:
            raise FileSystemError(
                f"There was an error renaming the file in the file system: {error}"
            ) from error

        return new_file_path

    def delete_file(self, user_id: int, filename: str) -> None:
        """Delete a file from the user's directory."""
        user_folder = self._user_folder(user_id)
        try:
            file_whole_path = user_folder / filename
            file_whole_path.unlink(missing_ok=True)
        except Exception as error:
            raise FileSystemError(
                f"There was an error removing the file from the file system: {error}"
            ) from error

    def open_for_reading(self, path: str | Path) -> IO[str]:
        """Open *path* for sequential text reading and return the file object."""
        return open(path, "r")
