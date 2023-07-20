import os
import shutil
import time
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

def getFileNameInFolder(current: str, searched: str) -> str:
    """
    - Name: getFileNameInFolder
    - Parameter(s):
        - current: string, path to the reference file
        - searched: string, file name of the searched file
    - Description:
        Generates the absolute path to a file in the same folder
    """
    return os.path.join(os.path.split(current)[0], searched)

def createFileName(filename: str) -> str:
    """
    - Name: createFileName
    - Parameter(s):
        - filename: string, file name to update
    - Description:
        Defines a secure filename to avoid repeated files
    """
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    file_base_name = os.path.splitext(filename)[0]
    file_extension = os.path.splitext(filename)[1].lower()
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
        user_files_folder_path = f'{FILES_FOLDER_PATH}\\{userId}'
        if not os.path.isdir(user_files_folder_path):
            os.makedirs(user_files_folder_path)

        # Save the file
        file_name = createFileName(fileName)
        file_path = os.path.join(user_files_folder_path, file_name)
        shutil.copy(original_path, file_path)
    except Exception as error:
        raise Exception('There was an error writing the file in the file system')

    return file_path

def renameFile(userId: int, filePath: str, newFileName: str) -> str:
    """
    - Name: renameFile
    - Parameter(s):
        - userId: int, user ID
        - filePath: string, path to the file we need to update
        - newFileName: string, file name for the final file
    - Description:
        Updates the name of a file in the file system
    """

    # Check if the file format is a valid one
    if not isAllowedFile(newFileName):
        raise Exception(f'Invalid file format, must be one of: {ALLOWED_FILE_EXTENSIONS}')

    try:
        # Rename the file
        current_file_path = f'{FILES_FOLDER_PATH}\\{filePath}'
        file_name = createFileName(newFileName)
        new_file_path = f'{FILES_FOLDER_PATH}\\{userId}\\{file_name}'
        os.rename(current_file_path, new_file_path)
    except Exception as error:
        raise Exception('There was an error renaming the file in the file system')

    return new_file_path

def deleteFile(filePath: str) -> None:
    """
    - Name: deleteFile
    - Parameter(s):
        - filePath: string, path to the file we need to remove
    - Description:
        Removes a file from the file system
    """
    try:
        # Remove the file
        file_whole_path = f'{FILES_FOLDER_PATH}/{filePath}'
        os.remove(file_whole_path)
    except Exception as error:
        raise Exception('There was an error removing the file from the file system')
