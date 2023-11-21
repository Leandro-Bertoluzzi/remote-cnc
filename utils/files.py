import shutil
import time
from pathlib import Path

try:
    from ..config import FILES_FOLDER_PATH
except ImportError:
    from config import FILES_FOLDER_PATH

ALLOWED_FILE_EXTENSIONS = {'txt', 'gcode', 'nc'}


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


def createFileName(filename: str) -> str:
    """
    - Name: createFileName
    - Parameter(s):
        - filename: string, file name to update
    - Description:
        Defines a secure filename to avoid repeated files
    """
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    file_base_name = Path(filename).stem
    file_extension = Path(filename).suffix.lower()
    return f'{file_base_name}_{timestamp}{file_extension}'


def saveFile(userId: int, original_path: str, fileName: str) -> str:
    """
    - Name: saveFile
    - Parameter(s):
        - userId: int, user ID
        - original_path: string, path to the file we need to save
        - filename: string, file name for the final file
    - Description:
        Copies a file into the right folder in the file system
    """

    # Check if the file format is a valid one
    if not isAllowedFile(fileName):
        raise Exception(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # If FILES_FOLDER_PATH or the folder for the current user are not present, then create them
        user_files_folder_path = Path(f'{FILES_FOLDER_PATH}/{userId}')
        if not user_files_folder_path.is_dir():
            user_files_folder_path.mkdir(parents=True)

        file_name = createFileName(fileName)

        # Save the file
        full_file_path = user_files_folder_path / file_name
        shutil.copy(original_path, full_file_path)
    except Exception as error:
        raise Exception(f'There was an error writing the file in the file system: {error}')

    return file_name


def renameFile(userId: int, fileName: str, newFileName: str) -> str:
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
        raise Exception(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # Rename the file
        current_file_path = Path(f'{FILES_FOLDER_PATH}/{userId}/{fileName}')
        file_name = createFileName(newFileName)
        full_file_path = Path(f'{FILES_FOLDER_PATH}/{userId}/{file_name}')
        current_file_path.rename(full_file_path)
    except Exception as error:
        raise Exception(f'There was an error renaming the file in the file system: {error}')

    return file_name


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
        file_whole_path.unlink()
    except Exception as error:
        raise Exception(f'There was an error removing the file from the file system: {error}')
