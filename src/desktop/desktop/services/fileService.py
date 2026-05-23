"""Service layer for File domain operations."""

import logging

from core.adapters.file_manager import FileManager
from core.adapters.file_storage import FileSystemStorage
from core.adapters.worker.worker_client import WorkerClient
from core.domain.entities import File
from core.ports.worker_client import IWorkerClient

from desktop.config import FILES_FOLDER_PATH
from desktop.services import get_db_session
from desktop.services.dependencies import get_file_repository

logger = logging.getLogger(__name__)

_worker_client: IWorkerClient | None = None


def _get_worker_client() -> IWorkerClient:
    global _worker_client  # noqa: PLW0603
    if _worker_client is None:
        _worker_client = WorkerClient.from_config()
    return _worker_client


class FileService:
    """Encapsulates all file-related operations (DB + filesystem + worker)."""

    @classmethod
    def get_all_files(cls) -> list[File]:
        with get_db_session() as session:
            repository = get_file_repository(session)
            return repository.get_all_files()

    @classmethod
    def create_file(cls, user_id: int, name: str, origin_path: str) -> File:
        """Create a file in DB + filesystem, then schedule report/thumbnail generation.

        If the broker is unavailable, the file is still created but the
        report and thumbnail will not be generated. A warning is logged.
        """
        with get_db_session() as session:
            repository = get_file_repository(session)
            file_manager = FileManager(repository, FileSystemStorage(FILES_FOLDER_PATH))
            file = file_manager.create_file(user_id, name, origin_path)

        # Schedule background tasks — broker failure should not prevent file creation
        try:
            client = _get_worker_client()
            client.generate_file_report(file.id)
            client.create_thumbnail(file.id)
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
            repository = get_file_repository(session)
            file_manager = FileManager(repository, FileSystemStorage(FILES_FOLDER_PATH))
            file_manager.rename_file(user_id, file, new_name)

    @classmethod
    def remove_file(cls, file: File) -> None:
        with get_db_session() as session:
            repository = get_file_repository(session)
            file_manager = FileManager(repository, FileSystemStorage(FILES_FOLDER_PATH))
            file_manager.remove_file(file)
