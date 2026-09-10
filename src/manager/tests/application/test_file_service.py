from unittest.mock import ANY, MagicMock

from core.domain.entities import File
from core.ports.file_storage import IFileStorage
from core.ports.worker_client import IWorkerClient
from manager.application.file_service import FileService
from pytest_mock.plugin import MockerFixture


class TestFileService:
    @staticmethod
    def _make_service_and_repo(worker=None, storage=None):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        repository = MagicMock()
        file_repo_factory = MagicMock(return_value=repository)

        mock_storage = storage if storage is not None else MagicMock(spec=IFileStorage)
        mock_worker = worker if worker is not None else MagicMock(spec=IWorkerClient)
        service = FileService(
            worker=mock_worker,
            storage=mock_storage,
            session_factory=session_factory,
            logger=MagicMock(),
            file_repo_factory=file_repo_factory,
        )
        return service, session, repository, mock_worker, mock_storage

    def test_get_all_files(self):
        service, _, repository, *_ = self._make_service_and_repo()
        expected_files = [MagicMock(spec=File), MagicMock(spec=File)]
        repository.get_all_files.return_value = expected_files

        result = service.get_all_files()

        assert result == expected_files
        repository.get_all_files.assert_called_once_with()

    def test_get_all_files_from_user(self):
        service, _, repository, *_ = self._make_service_and_repo()
        expected_files = [MagicMock(spec=File)]
        repository.get_all_files_from_user.return_value = expected_files

        result = service.get_all_files_from_user(5)

        assert result == expected_files
        repository.get_all_files_from_user.assert_called_once_with(5)

    def test_get_file_by_id(self):
        service, _, repository, *_ = self._make_service_and_repo()
        expected_file = MagicMock(spec=File)
        repository.get_file_by_id.return_value = expected_file

        result = service.get_file_by_id(12)

        assert result == expected_file
        repository.get_file_by_id.assert_called_once_with(12)

    def test_read_file(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo()
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        file_manager_cls.return_value.read_file.return_value = "G21\n"

        result = service.read_file(12)

        assert result == "G21\n"
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.read_file.assert_called_once_with(12)

    def test_rename_file(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo()
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        file_obj = MagicMock(spec=File)

        service.rename_file(user_id=5, file=file_obj, new_name="renamed.gcode")

        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.rename_file.assert_called_once_with(
            5, file_obj, "renamed.gcode"
        )

    def test_rename_file_by_id(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo()
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        file_obj = MagicMock(spec=File)
        repository.get_file_by_id.return_value = file_obj

        result = service.rename_file_by_id(5, 12, "renamed.gcode")

        assert result == file_manager_cls.return_value.rename_file.return_value
        repository.get_file_by_id.assert_called_once_with(12)
        file_manager_cls.return_value.rename_file.assert_called_once_with(
            5, file_obj, "renamed.gcode"
        )

    def test_remove_file(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo()
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        file_obj = MagicMock(spec=File)

        service.remove_file(file_obj)

        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.remove_file.assert_called_once_with(file_obj)

    def test_remove_file_by_id(self, mocker: MockerFixture):
        service, _, repository, *_ = self._make_service_and_repo()
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        file_obj = MagicMock(spec=File)
        repository.get_file_by_id.return_value = file_obj

        service.remove_file_by_id(12)

        repository.get_file_by_id.assert_called_once_with(12)
        file_manager_cls.return_value.remove_file.assert_called_once_with(file_obj)

    def test_create_file_schedules_worker_tasks(self, mocker: MockerFixture):
        worker = MagicMock(spec=IWorkerClient)
        service, _, repository, *_ = self._make_service_and_repo(worker=worker)
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
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
        service, _, repository, *_ = self._make_service_and_repo(worker=worker)
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        created_file = MagicMock(spec=File)
        created_file.id = 10
        file_manager_cls.return_value.create_file.return_value = created_file

        result = service.create_file(1, "piece.gcode", "/tmp/piece.gcode")

        assert result == created_file
        file_manager_cls.assert_called_once_with(repository, ANY)
        worker.generate_file_report.assert_called_once_with(10)
        worker.create_thumbnail.assert_not_called()

    def test_upload_file_schedules_worker_tasks(self, mocker: MockerFixture):
        worker = MagicMock(spec=IWorkerClient)
        service, _, repository, *_ = self._make_service_and_repo(worker=worker)
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        uploaded_file = MagicMock(spec=File)
        uploaded_file.id = 20
        file_manager_cls.return_value.upload_file.return_value = uploaded_file

        result = service.upload_file(1, "piece.gcode", MagicMock())

        assert result == uploaded_file
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.upload_file.assert_called_once_with(1, "piece.gcode", ANY)
        worker.generate_file_report.assert_called_once_with(20)
        worker.create_thumbnail.assert_called_once_with(20)

    def test_upload_file_worker_failure_still_returns_file(self, mocker: MockerFixture):
        worker = MagicMock(spec=IWorkerClient)
        worker.generate_file_report.side_effect = RuntimeError("broker unavailable")
        service, _, repository, *_ = self._make_service_and_repo(worker=worker)
        file_manager_cls = mocker.patch("manager.application.file_service.FileManager")
        uploaded_file = MagicMock(spec=File)
        uploaded_file.id = 20
        file_manager_cls.return_value.upload_file.return_value = uploaded_file

        result = service.upload_file(1, "piece.gcode", MagicMock())

        assert result == uploaded_file
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.upload_file.assert_called_once_with(1, "piece.gcode", ANY)
        worker.generate_file_report.assert_called_once_with(20)
        worker.create_thumbnail.assert_not_called()
