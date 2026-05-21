from contextlib import suppress
from pathlib import Path

ALLOWED_FILE_EXTENSIONS = {"txt", "gcode", "nc"}

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


def getFilesInFolder(folderPath: str) -> list[str]:
    desktop = Path(folderPath)
    return [item.name for item in desktop.iterdir()]


def changeFileExtension(file_path: str, new_extension: str) -> str:
    path = Path(file_path)
    new_file_path = path.with_suffix("." + new_extension)
    return str(new_file_path)


def createFileIfNotExists(file_path: str):
    with suppress(FileExistsError), open(file_path, "x") as file:
        file.write("")
