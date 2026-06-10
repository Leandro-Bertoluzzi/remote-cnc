from unittest.mock import ANY, MagicMock

from core.domain.entities import File
from core.ports.file_storage import IFileStorage
from core.ports.worker_client import IWorkerClient
from desktop.services.fileService import FileService
from pytest_mock.plugin import MockerFixture


class TestFileService:
    @staticmethod
    def _make_service_and_repo(mocker: MockerFixture, worker=None, storage=None):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        repository = MagicMock()
        mocker.patch(
            "desktop.services.fileService.get_file_repository",
            return_value=repository,
        )

        mock_storage = storage if storage is not None else MagicMock(spec=IFileStorage)
        mock_worker = worker if worker is not None else MagicMock(spec=IWorkerClient)
        service = FileService(
            worker=mock_worker,
            storage=mock_storage,
            session_factory=session_factory,
            logger=MagicMock(),
        )
        return service, session, repository, mock_worker, mock_storage

    def test_get_all_files(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo(mocker)
        expected_files = [MagicMock(spec=File), MagicMock(spec=File)]
        repository.get_all_files.return_value = expected_files

        result = service.get_all_files()

        assert result == expected_files
        repository.get_all_files.assert_called_once_with()

    def test_rename_file(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        file_obj = MagicMock(spec=File)

        service.rename_file(user_id=5, file=file_obj, new_name="renamed.gcode")

        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.rename_file.assert_called_once_with(
            5, file_obj, "renamed.gcode"
        )

    def test_remove_file(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        file_obj = MagicMock(spec=File)

        service.remove_file(file_obj)

        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.remove_file.assert_called_once_with(file_obj)

    def test_create_file_schedules_worker_tasks(self, mocker: MockerFixture):
        worker = MagicMock(spec=IWorkerClient)
        service, _, repository, *_ = self._make_service_and_repo(mocker, worker=worker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        created_file = MagicMock(spec=File)
        created_file.id = 10
        file_manager_cls.return_value.create_file.return_value = created_file

        result = service.create_file(1, "piece.gcode", "/tmp/piece.gcode")

        assert result == created_file
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.create_file.assert_called_once_with(
            1, "piece.gcode", "/tmp/piece.gcode"
        )
        worker.generate_file_report.assert_called_once_with(10)
        worker.create_thumbnail.assert_called_once_with(10)

    def test_create_file_worker_failure_still_returns_file(self, mocker: MockerFixture):
        worker = MagicMock(spec=IWorkerClient)
        worker.generate_file_report.side_effect = RuntimeError("broker unavailable")
        service, _, repository, *_ = self._make_service_and_repo(mocker, worker=worker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        created_file = MagicMock(spec=File)
        created_file.id = 10
        file_manager_cls.return_value.create_file.return_value = created_file

        result = service.create_file(1, "piece.gcode", "/tmp/piece.gcode")

        assert result == created_file
        file_manager_cls.assert_called_once_with(repository, ANY)
        worker.generate_file_report.assert_called_once_with(10)
        worker.create_thumbnail.assert_not_called()
