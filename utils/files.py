import shutil
import hashlib
from pathlib import Path
from typing import BinaryIO

try:
    from ..config import FILES_FOLDER_PATH
except ImportError:
    from config import FILES_FOLDER_PATH

ALLOWED_FILE_EXTENSIONS = {'txt', 'gcode', 'nc'}

# Custom exceptions


class InvalidFile(Exception):
    pass


class FileSystemError(Exception):
    pass


def isAllowedFile(filename: str) -> bool:
    """
    - Name: isAllowedFile
    - Parameter(s):
        - filename: string, file name to validate
    - Description:
        Checks if the file has a valid file extension
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS


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


def getFilePath(basePath: str, userId: int, fileName: str) -> Path:
    """
    - Name: getFilePath
    - Parameter(s):
        - basePath: string, absolute path to parent folder
        - userId: int, user ID
        - fileName: string, name of the file we need to remove
    - Description:
        Returns the path to the user's file
    """
    return Path(basePath, FILES_FOLDER_PATH, str(userId), fileName)


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


def saveFile(userId: int, file: BinaryIO, filename: str) -> Path:
    """ Copies a file into the right folder in the file system
    - Parameter(s):
        - userId: int, user ID
        - file: BinaryIO, content of the file to save in system
        - filename: string, file name of the original file
    """

    # Check if the file format is a valid one
    if not isAllowedFile(filename):
        raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # If FILES_FOLDER_PATH or the folder for the current user are not present, then create them
        user_files_folder_path = Path(f'{FILES_FOLDER_PATH}/{userId}')
        if not user_files_folder_path.is_dir():
            user_files_folder_path.mkdir(parents=True)

        # Save the file
        full_file_path = user_files_folder_path / filename
        with open(full_file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
    except Exception as error:
        raise FileSystemError(f'There was an error writing the file in the file system: {error}')

    return full_file_path


def copyFile(userId: int, original_path: str, fileName: str) -> Path:
    """ Copies a file into the right folder in the file system
    - Parameter(s):
        - userId: int, user ID
        - original_path: string, path to the file we need to save
        - filename: string, file name for the final file
    """

    # Check if the file format is a valid one
    if not isAllowedFile(fileName):
        raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # If FILES_FOLDER_PATH or the folder for the current user are not present, then create them
        user_files_folder_path = Path(f'{FILES_FOLDER_PATH}/{userId}')
        if not user_files_folder_path.is_dir():
            user_files_folder_path.mkdir(parents=True)

        # Save the file
        full_file_path = user_files_folder_path / fileName
        shutil.copy(original_path, full_file_path)
    except Exception as error:
        raise FileSystemError(f'There was an error writing the file in the file system: {error}')

    return full_file_path


def renameFile(userId: int, fileName: str, newFileName: str) -> Path:
    """
    - Name: renameFile
    - Parameter(s):
        - userId: int, user ID
        - fileName: string, name of the file we need to update
        - newFileName: string, file name for the final file
    - Description:
        Updates the name of a file in the file system
    """

    # Check if the file format is a valid one
    if not isAllowedFile(newFileName):
        raise InvalidFile(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # Rename the file
        current_file_path = Path(f'{FILES_FOLDER_PATH}/{userId}/{fileName}')
        full_file_path = Path(f'{FILES_FOLDER_PATH}/{userId}/{newFileName}')
        current_file_path.rename(full_file_path)
    except Exception as error:
        raise FileSystemError(f'There was an error renaming the file in the file system: {error}')

    return full_file_path


def deleteFile(userId: int, fileName: str) -> None:
    """
    - Name: deleteFile
    - Parameter(s):
        - userId: int, user ID
        - fileName: string, name of the file we need to remove
    - Description:
        Removes a file from the file system
    """
    try:
        # Remove the file
        file_whole_path = Path(f'{FILES_FOLDER_PATH}/{userId}/{fileName}')
        file_whole_path.unlink(missing_ok=True)
    except Exception as error:
        raise FileSystemError(f'There was an error removing the file from the file system: {error}')
