"""Service layer for File domain operations."""

import logging

from core.database.models import File
from core.database.repositories.fileRepository import FileRepository
from core.utilities.fileManager import FileManager
from core.utilities.worker.scheduler import create_thumbnail, generate_file_report

from desktop.config import FILES_FOLDER_PATH
from desktop.services import get_db_session

logger = logging.getLogger(__name__)


class FileService:
    """Encapsulates all file-related operations (DB + filesystem + Celery)."""

    @classmethod
    def get_all_files(cls) -> list[File]:
        with get_db_session() as session:
            repository = FileRepository(session)
            return repository.get_all_files()

    @classmethod
    def create_file(cls, user_id: int, name: str, origin_path: str) -> File:
        """Create a file in DB + filesystem, then schedule report/thumbnail generation.

        If the broker is unavailable, the file is still created but the
        report and thumbnail will not be generated. A warning is logged.
        """
        with get_db_session() as session:
            file_manager = FileManager(FILES_FOLDER_PATH, session)
            file = file_manager.create_file(user_id, name, origin_path)

        # Schedule background tasks — broker failure should not prevent file creation
        try:
            generate_file_report(file.id)
            create_thumbnail(file.id)
        except Exception:
            logger.warning(
                "No se pudo programar la generación de reporte/thumbnail para archivo %s. "
                "El archivo fue creado correctamente.",
                file.id,
            )

        return file

    @classmethod
    def rename_file(cls, user_id: int, file: File, new_name: str) -> None:
        with get_db_session() as session:
            file_manager = FileManager(FILES_FOLDER_PATH, session)
            file_manager.rename_file(user_id, file, new_name)

    @classmethod
    def remove_file(cls, file: File) -> None:
        with get_db_session() as session:
            file_manager = FileManager(FILES_FOLDER_PATH, session)
            file_manager.remove_file(file)
