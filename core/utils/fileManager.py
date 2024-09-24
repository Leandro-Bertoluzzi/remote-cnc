from pathlib import Path
import shutil
from sqlalchemy.orm import Session
from typing import BinaryIO

try:
    from database.models import File
    from database.repositories.fileRepository import FileRepository
    from utils.files import computeSHA256, computeSHA256FromFile, FileSystemHelper
except ImportError:
    from ..database.models import File
    from ..database.repositories.fileRepository import FileRepository
    from .files import computeSHA256, computeSHA256FromFile, FileSystemHelper


class FileManager:
    def __init__(self, base_path, _session: Session):
        self.base_path = base_path
        self.session = _session

    def read_file(self, file_id: int) -> str:
        """Reads the content of a file in the FS.

        Arguments:
        - file_id (int): File ID.

        Returns: file content (str)

        Raises:
        - DatabaseError: Error from ORM.
        - EntityNotFoundError: The file was not found in the DB.
        - FileSystemError: An error ocurred while reading.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Checks if the file is repeated
        # can raise (DatabaseError, EntityNotFoundError)
        file = repository.get_file_by_id(file_id)

        # Save file in the file system
        # Can raise FileSystemError
        files_helper = FileSystemHelper(self.base_path)
        return files_helper.readFile(file.user_id, file.file_name)

    def upload_file(self, user_id: int, file_name: str, file: BinaryIO) -> File:
        """Creates a file in the FS and saves it to the DB.
        It either FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - user_id (int): User ID.
        - file_name (str): File name of the new file.
        - origin_path (str): File path to the original file.

        Returns: file_id (int)

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists for the current user.
        - DuplicatedFileError: A file with the same content already exists for the current user.
        - DatabaseError: Error from ORM.
        - InvalidFile: Invalid file extension.
        - FileSystemError: An error ocurred during file creation in FS.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Checks if the file is repeated
        # can raise (DuplicatedFileNameError, DuplicatedFileError)
        file_hash = computeSHA256FromFile(file)
        repository.check_file_exists(user_id, file_name, file_hash)

        # Save file in the file system
        # Can raise (InvalidFile, FileSystemError)
        files_helper = FileSystemHelper(self.base_path)
        created_path = files_helper.saveFile(user_id, file, file_name)

        # Create an entry for the file in the DB
        # Can raise DatabaseError
        try:
            return repository.create_file(user_id, file_name, file_hash)
        except Exception as error:
            self._rollback_created(created_path)
            raise error

    def create_file(self, user_id: int, file_name: str, origin_path: str) -> int:
        """Creates a file in the FS and saves it to the DB.
        It either FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - user_id (int): User ID.
        - file_name (str): File name of the new file.
        - origin_path (str): File path to the original file.

        Returns: file_id (int)

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists for the current user.
        - DuplicatedFileError: A file with the same content already exists for the current user.
        - DatabaseError: Error from ORM.
        - InvalidFile: Invalid file extension.
        - FileSystemError: An error ocurred during file creation in FS.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Checks if the file is repeated
        # can raise (DuplicatedFileNameError, DuplicatedFileError)
        file_hash = computeSHA256(origin_path)
        repository.check_file_exists(user_id, file_name, file_hash)

        # Save file in the file system
        # Can raise (InvalidFile, FileSystemError)
        files_helper = FileSystemHelper(self.base_path)
        created_path = files_helper.copyFile(user_id, origin_path, file_name)

        # Create an entry for the file in the DB
        # Can raise DatabaseError
        try:
            new_file = repository.create_file(user_id, file_name, file_hash)
            return new_file.id
        except Exception as error:
            self._rollback_created(created_path)
            raise error

    def rename_file(self, user_id: int, file: File, new_name: str):
        """Renames a file in the FS and update it in the DB.
        It either FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - user_id (int): User ID.
        - file (File): Current file in DB.
        - new_name (str): New file name for the file.

        Returns: None

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists for the current user.
        - InvalidFile: Invalid file extension.
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error ocurred during file update in FS.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Check if the file is repeated
        # can raise DuplicatedFileNameError
        repository.check_file_exists(user_id, new_name, 'impossible-hash')

        # Save the original file name, in case we have to recover it
        files_helper = FileSystemHelper(self.base_path)
        original_path = files_helper.getFilePath(
            file.user_id,
            file.file_name
        )

        # Update file in the file system
        # Can raise (InvalidFile, FileSystemError)
        updated_path = files_helper.renameFile(
            file.user_id,
            file.file_name,
            new_name
        )

        # Update the entry for the file in the DB
        # Can raise (EntityNotFoundError, DatabaseError)
        try:
            return repository.update_file(file.id, file.user_id, new_name)
        except Exception as error:
            self._rollback_renamed(updated_path, original_path)
            raise error

    def rename_file_by_id(self, user_id: int, file_id: int, new_name: str):
        """Renames a file in the FS and update it in the DB.
        It either FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - user_id (int): User ID.
        - file (File): Current file in DB.
        - new_name (str): New file name for the file.

        Returns: None

        Raises:
        - DuplicatedFileNameError: A file with the same name already exists for the current user.
        - InvalidFile: Invalid file extension.
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error ocurred during file update in FS.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Get file
        # Can raise (EntityNotFoundError, DatabaseError)
        file = repository.get_file_by_id(file_id)

        # Original method
        return self.rename_file(user_id, file, new_name)

    def remove_file(self, file: File):
        """Removes a file from the FS and the DB.
        If the FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - file (File): Current file in DB.

        Returns: None

        Raises:
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error ocurred during file removal in FS.
        """
        # Save a backup of the file, in case we have to recover it
        files_helper = FileSystemHelper(self.base_path)
        file_path = files_helper.getFilePath(
            file.user_id,
            file.file_name
        )
        self._backup_file(file_path)

        # Remove the file from the file system
        # Can raise FileSystemError
        files_helper.deleteFile(file.user_id, file.file_name)

        # Remove the entry for the file in the DB
        repository = FileRepository(self.session)

        # Remove the entry for the file in the DB
        # Can raise (EntityNotFoundError, DatabaseError)
        try:
            repository.remove_file(file.id)
        except Exception as error:
            self._rollback_removed(file_path)
            raise error

        self._remove_backup()

    def remove_file_by_id(self, file_id: int):
        """Removes a file from the FS and the DB.
        If the FS or DB raises an error, it rollbacks the whole operation.

        Arguments:
        - file (File): Current file in DB.

        Returns: None

        Raises:
        - EntityNotFoundError: The file was not found in the DB.
        - DatabaseError: Error from ORM.
        - FileSystemError: An error ocurred during file removal in FS.
        """
        # Instantiate repository
        repository = FileRepository(self.session)

        # Get file
        # Can raise (EntityNotFoundError, DatabaseError)
        file = repository.get_file_by_id(file_id)

        # Original method
        self.remove_file(file)

    # UTILITIES

    def _rollback_created(self, file_path: Path):
        file_path.unlink(missing_ok=True)

    def _rollback_renamed(self, file_path: Path, old_name: str):
        file_path.rename(old_name)

    def _rollback_removed(self, file_path: Path):
        try:
            shutil.move(self.backup_path, file_path)
        except Exception:
            pass

    def _backup_file(self, file_path: Path):
        if not file_path.exists():
            return
        self.backup_path = file_path.parent.parent / (file_path.name + ".backup")
        shutil.copy(file_path, self.backup_path)

    def _remove_backup(self):
        try:
            self.backup_path.unlink(missing_ok=True)
        except Exception:
            pass
