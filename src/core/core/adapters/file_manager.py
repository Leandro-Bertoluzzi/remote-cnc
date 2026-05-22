"""FileManager — application-layer adapter combining DB and file storage.

Coordinates ``IFileRepository`` (DB port) and ``IFileStorage`` (filesystem) to
provide transactional file operations with automatic rollback on failure.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO

from core.database.models import File
from core.ports.file_repository import IFileRepository
from core.ports.file_storage import IFileStorage


class FileManager:
    def __init__(self, file_repository: IFileRepository, file_storage: IFileStorage):
        self.file_repository = file_repository
        self.file_storage = file_storage

    def read_file(self, file_id: int) -> str:
        """Read the content of a file in the FS.

        Raises:
        - DatabaseError: Error from ORM.
        - EntityNotFoundError: The file was not found in the DB.
        - FileSystemError: An error occurred while reading.
        """
        file = self.file_repository.get_file_by_id(file_id)
        return self.file_storage.read_file(file.user_id, file.file_name)

    def upload_file(self, user_id: int, file_name: str, file: BinaryIO) -> File:
        """Create a file in the FS from an upload and save it to the DB.

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists.
        - DuplicatedFileError: A file with the same content already exists.
        - DatabaseError: Error from ORM.
        - InvalidFile: Invalid file extension.
        - FileSystemError: An error occurred during file creation in FS.
        """
        repository = self.file_repository
        file_hash = self._compute_hash_from_file(file)
        repository.check_file_exists(user_id, file_name, file_hash)

        created_path = self.file_storage.save_file(user_id, file, file_name)
        try:
            return repository.create_file(user_id, file_name, file_hash)
        except Exception as error:
            self._rollback_created(created_path)
            raise error

    def create_file(self, user_id: int, file_name: str, origin_path: str) -> File:
        """Create a file in the FS from another file and save it to the DB.

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists.
        - DuplicatedFileError: A file with the same content already exists.
        - DatabaseError: Error from ORM.
        - InvalidFile: Invalid file extension.
        - FileSystemError: An error occurred during file creation in FS.
        """
        repository = self.file_repository
        file_hash = self._compute_hash(origin_path)
        repository.check_file_exists(user_id, file_name, file_hash)

        created_path = self.file_storage.copy_file(user_id, origin_path, file_name)
        try:
            return repository.create_file(user_id, file_name, file_hash)
        except Exception as error:
            self._rollback_created(created_path)
            raise error

    def rename_file(self, user_id: int, file: File, new_name: str) -> File:
        """Rename a file in the FS and update it in the DB.

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists.
        - InvalidFile: Invalid file extension.
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error occurred during file update in FS.
        """
        repository = self.file_repository
        repository.check_file_exists(user_id, new_name, "impossible-hash")

        original_path = self.file_storage.get_file_path(file.user_id, file.file_name)
        updated_path = self.file_storage.rename_file(file.user_id, file.file_name, new_name)
        try:
            return repository.update_file(file.id, file.user_id, new_name)
        except Exception as error:
            self._rollback_renamed(updated_path, original_path)
            raise error

    def rename_file_by_id(self, user_id: int, file_id: int, new_name: str) -> File:
        """Rename a file by its DB ID.

        Raises:
        - DuplicatedFileNameError, InvalidFile, EntityNotFoundError, DatabaseError, FileSystemError.
        """
        file = self.file_repository.get_file_by_id(file_id)
        return self.rename_file(user_id, file, new_name)

    def remove_file(self, file: File) -> None:
        """Remove a file from the FS and the DB.

        Raises:
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error occurred during file removal in FS.
        """
        file_path = self.file_storage.get_file_path(file.user_id, file.file_name)
        self._backup_file(file_path)

        self.file_storage.delete_file(file.user_id, file.file_name)

        try:
            self.file_repository.remove_file(file.id)
        except Exception as error:
            self._rollback_removed(file_path)
            raise error

        self._remove_backup()

    def remove_file_by_id(self, file_id: int) -> None:
        """Remove a file by its DB ID.

        Raises:
        - EntityNotFoundError, DatabaseError, FileSystemError.
        """
        file = self.file_repository.get_file_by_id(file_id)
        self.remove_file(file)

    # ------------------------------------------------------------------
    # Rollback helpers
    # ------------------------------------------------------------------

    def _rollback_created(self, file_path: Path) -> None:
        file_path.unlink(missing_ok=True)

    def _rollback_renamed(self, file_path: Path, old_name: str | Path) -> None:
        file_path.rename(old_name)

    def _rollback_removed(self, file_path: Path) -> None:
        try:
            shutil.move(self.backup_path, file_path)
        except Exception:
            pass

    def _backup_file(self, file_path: Path) -> None:
        if not file_path.exists():
            return
        self.backup_path = file_path.parent.parent / (file_path.name + ".backup")
        shutil.copy(file_path, self.backup_path)

    def _remove_backup(self) -> None:
        try:
            self.backup_path.unlink(missing_ok=True)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Hashing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_hash_from_file(file: BinaryIO) -> str:
        """Return the SHA-256 hex digest of an open binary file, resetting the pointer."""
        h = hashlib.sha256()
        for chunk in iter(lambda: file.read(4096), b""):
            h.update(chunk)
        file.seek(0)
        return h.hexdigest()

    @staticmethod
    def _compute_hash(file_path: str) -> str:
        """Return the SHA-256 hex digest of a file at *file_path*."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
