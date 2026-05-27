"""Service layer for File domain operations."""

import logging

from core.application.file_manager import FileManager
from core.domain.entities import File
from core.ports.db_session import SessionFactory
from core.ports.file_storage import IFileStorage
from core.ports.worker_client import IWorkerClient

from desktop.services.dependencies import get_file_repository

logger = logging.getLogger(__name__)


class FileService:
    """Encapsulates all file-related operations (DB + filesystem + worker)."""

    def __init__(
        self,
        worker: IWorkerClient,
        storage: IFileStorage,
        session_factory: SessionFactory,
    ):
        self._worker = worker
        self._storage = storage
        self._session_factory = session_factory

    def get_all_files(self) -> list[File]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_file_repository(session)
            return repository.get_all_files()

    def create_file(self, user_id: int, name: str, origin_path: str) -> File:
        """Create a file in DB + filesystem, then schedule report/thumbnail generation.

        If the broker is unavailable, the file is still created but the
        report and thumbnail will not be generated. A warning is logged.
        """
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_file_repository(session)
            file_manager = FileManager(repository, self._storage)
            file = file_manager.create_file(user_id, name, origin_path)

        # Schedule background tasks — broker failure should not prevent file creation
        try:
            self._worker.generate_file_report(file.id)
            self._worker.create_thumbnail(file.id)
        except Exception:
            logger.warning(
                "No se pudo programar la generación de reporte/thumbnail para archivo %s. "
                "El archivo fue creado correctamente.",
                file.id,
            )

        return file

    def rename_file(self, user_id: int, file: File, new_name: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_file_repository(session)
            file_manager = FileManager(repository, self._storage)
            file_manager.rename_file(user_id, file, new_name)

    def remove_file(self, file: File) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_file_repository(session)
            file_manager = FileManager(repository, self._storage)
            file_manager.remove_file(file)
