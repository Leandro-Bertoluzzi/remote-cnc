"""Application service for File domain operations."""

from collections.abc import Callable
from typing import BinaryIO

from core.application.file_manager import FileManager
from core.domain.entities import File
from core.ports.db_session import DbSession, SessionFactory
from core.ports.file_repository import IFileRepository
from core.ports.file_storage import IFileStorage
from core.ports.logger import ILogger
from core.ports.worker_client import IWorkerClient


class FileService:
    """Encapsulates all file-related operations (DB + filesystem + worker)."""

    def __init__(
        self,
        worker: IWorkerClient,
        storage: IFileStorage,
        session_factory: SessionFactory,
        logger: ILogger,
        file_repo_factory: Callable[[DbSession], IFileRepository],
    ):
        self._worker = worker
        self._storage = storage
        self._session_factory = session_factory
        self._logger = logger
        self._file_repo_factory = file_repo_factory

    def get_all_files(self) -> list[File]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            return repository.get_all_files()

    def get_all_files_from_user(self, user_id: int) -> list[File]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            return repository.get_all_files_from_user(user_id)

    def get_file_by_id(self, file_id: int) -> File:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            return repository.get_file_by_id(file_id)

    def read_file(self, file_id: int) -> str:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            return file_manager.read_file(file_id)

    def upload_file(self, user_id: int, name: str, file: BinaryIO) -> File:
        """Upload a file, then schedule report/thumbnail generation.

        If the broker is unavailable, the file is still created but the
        report and thumbnail will not be generated. A warning is logged.
        """
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            file = file_manager.upload_file(user_id, name, file)

        # Schedule background tasks — broker failure should not prevent file creation
        if file.id is None:
            self._logger.error(
                "Archivo creado sin ID - no se puede programar generación de reporte/thumbnail"
            )
            return file

        try:
            self._worker.generate_file_report(file.id)
            self._worker.create_thumbnail(file.id)
        except Exception:
            self._logger.warning(
                "No se pudo programar la generación de reporte/thumbnail para archivo %s. "
                "El archivo fue creado correctamente.",
                file.id,
            )

        return file

    def create_file(self, user_id: int, name: str, origin_path: str) -> File:
        """Create a file, then schedule report/thumbnail generation.

        If the broker is unavailable, the file is still created but the
        report and thumbnail will not be generated. A warning is logged.
        """
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            file = file_manager.create_file(user_id, name, origin_path)

        # Schedule background tasks — broker failure should not prevent file creation
        if file.id is None:
            self._logger.error(
                "Archivo creado sin ID - no se puede programar generación de reporte/thumbnail"
            )
            return file

        try:
            self._worker.generate_file_report(file.id)
            self._worker.create_thumbnail(file.id)
        except Exception:
            self._logger.warning(
                "No se pudo programar la generación de reporte/thumbnail para archivo %s. "
                "El archivo fue creado correctamente.",
                file.id,
            )

        return file

    def rename_file(self, user_id: int, file: File, new_name: str) -> File:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            return file_manager.rename_file(user_id, file, new_name)

    def rename_file_by_id(self, user_id: int, file_id: int, new_name: str) -> File:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            file = repository.get_file_by_id(file_id)
            return file_manager.rename_file(user_id, file, new_name)

    def remove_file(self, file: File) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            file_manager.remove_file(file)

    def remove_file_by_id(self, file_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._file_repo_factory(session)
            file_manager = FileManager(repository, self._storage)
            file = repository.get_file_by_id(file_id)
            file_manager.remove_file(file)

    def generate_file_report(self, file_id: int) -> None:
        self._worker.generate_file_report(file_id)

    def create_thumbnail(self, file_id: int) -> None:
        self._worker.create_thumbnail(file_id)
