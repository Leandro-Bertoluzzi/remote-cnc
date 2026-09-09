"""FastAPI dependency providing a ready-to-use ``FileManager`` instance."""

from typing import Annotated

from core.adapters.file_storage import FileSystemStorage
from core.application.file_manager import FileManager
from core.config import FILES_FOLDER_PATH
from fastapi import Depends
from manager.adapters.api.middleware.dbMiddleware import GetFileRepository


def get_file_manager(repository: GetFileRepository) -> FileManager:
    """Build a ``FileManager`` with the request-scoped repository."""
    return FileManager(repository, FileSystemStorage(FILES_FOLDER_PATH))


GetFileManager = Annotated[FileManager, Depends(get_file_manager)]
