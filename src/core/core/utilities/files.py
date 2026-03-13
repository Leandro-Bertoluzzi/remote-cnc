import shutil
import hashlib
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO

ALLOWED_FILE_EXTENSIONS = {'txt', 'gcode', 'nc'}

# Custom exceptions


class InvalidFile(Exception):
    pass


class FileSystemError(Exception):
    pass


def getFileNameInFolder(current: str, searched: str) -> Path:
    """
    - Name: getFileNameInFolder
    - Parameter(s):
        - current: string, path to the reference file
        - searched: string, file name of the searched file
    - Description:
        Generates the absolute path to a file in the same folder
    """
    folder = Path(current).parent
    return folder / searched


def computeSHA256FromFile(file: BinaryIO) -> str:
    """
    - Name: computeSHA256FromFile
    - Parameter(s):
        - file: reference file
    - Description:
        Generates SHA256 hash from the content of the file
    """
    hash_sha256 = hashlib.sha256()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_sha256.update(chunk)

    # Once finished, reset the file pointer
    file.seek(0)
    return hash_sha256.hexdigest()


def computeSHA256(filePath: str) -> str:
    """
    - Name: computeSHA256
    - Parameter(s):
        - filePath: path to the reference file
    - Description:
        Generates SHA256 hash from the content of the file
    """
    hash_sha256 = hashlib.sha256()
    with open(filePath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def getFilesInFolder(folderPath: str) -> list[str]:
    desktop = Path(folderPath)
    return [item.name for item in desktop.iterdir()]


def changeFileExtension(file_path: str, new_extension: str) -> str:
    path = Path(file_path)
    new_file_path = path.with_suffix("." + new_extension)
    return str(new_file_path)


def createFileIfNotExists(file_path: str):
    with suppress(FileExistsError), open(file_path, 'x') as file:
        file.write("")


class FileSystemHelper:
    def __init__(self, base_path: str | Path):
        """
        - Parameter(s):
            - base_path: absolute path to files folder
        """
        self.base_path = Path(base_path)

    # PRIVATE METHODS
    @staticmethod
    def _is_valid_filename(filename: str) -> bool:
        """
        - Name: _is_valid_filename
        - Parameter(s):
            - filename: string, file name to validate
        - Description:
            Checks if the file has a valid file extension
        """
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

    def _user_folder(self, user_id: int) -> Path:
        """Returns the path to the user's folder, creating it if necessary."""
        folder = self.base_path / str(user_id)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    # PUBLIC METHODS
    def get_file_path(self, user_id: int, filename: str) -> Path:
        """
        - Name: get_file_path
        - Parameter(s):
            - user_id: int, user ID
            - filename: string, name of the file we need to remove
        - Description:
            Returns the path to the user's file
        """
        return self.base_path / str(user_id) / filename

    def save_file(self, user_id: int, file: BinaryIO, filename: str) -> Path:
        """Creates a file into the right folder in the file system, with the given content."""

        # Check if the file format is a valid one
        if not self._is_valid_filename(filename):
            raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

        destination = self._user_folder(user_id) / filename
        try:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file, buffer)
        except Exception as error:
            raise FileSystemError(
                f'There was an error writing the file in the file system: {error}'
            )

        return destination

    def copy_file(self, user_id: int, original_path: str, filename: str) -> Path:
        """Copies a file into the right folder in the file system."""

        # Check if the file format is a valid one
        if not self._is_valid_filename(filename):
            raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

        destination = self._user_folder(user_id) / filename
        try:
            shutil.copy(original_path, destination)
        except Exception as error:
            raise FileSystemError(
                f'There was an error writing the file in the file system: {error}'
            )

        return destination

    def rename_file(self, user_id: int, filename: str, new_filename: str) -> Path:
        """Updates the name of a file in the file system."""

        # Check if the file format is a valid one
        if not self._is_valid_filename(new_filename):
            raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

        user_folder = self._user_folder(user_id)
        try:
            current_file_path = user_folder / filename
            new_file_path = user_folder / new_filename
            current_file_path.rename(new_file_path)
        except Exception as error:
            raise FileSystemError(
                f'There was an error renaming the file in the file system: {error}'
            )

        return new_file_path

    def delete_file(self, user_id: int, filename: str) -> None:
        """Removes a file from the file system."""

        user_folder = self._user_folder(user_id)
        try:
            file_whole_path = user_folder / filename
            file_whole_path.unlink(missing_ok=True)
        except Exception as error:
            raise FileSystemError(
                f'There was an error removing the file from the file system: {error}'
            )

    def read_file(self, user_id: int, filename: str) -> str:
        """Reads the content of a file in the file system."""

        file_path = self.get_file_path(user_id, filename)
        try:
            with open(file_path, "r") as content:
                return content.read()
        except Exception as error:
            raise FileSystemError(
                f'There was an error reading the file: {error}'
            )
