from unittest.mock import ANY, MagicMock

from core.database.models import File
from desktop.services.fileService import FileService
from pytest_mock.plugin import MockerFixture


class TestFileService:
    @staticmethod
    def _mock_db_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.fileService.get_db_session", return_value=session_ctx)
        repository = MagicMock()
        get_repo = mocker.patch(
            "desktop.services.fileService.get_file_repository",
            return_value=repository,
        )
        return session, repository, get_repo

    def test_get_all_files(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected_files = [MagicMock(spec=File), MagicMock(spec=File)]
        repository.get_all_files.return_value = expected_files

        result = FileService.get_all_files()

        assert result == expected_files
        get_repo.assert_called_once_with(session)
        repository.get_all_files.assert_called_once_with()

    def test_rename_file(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        file_obj = MagicMock(spec=File)

        FileService.rename_file(user_id=5, file=file_obj, new_name="renamed.gcode")

        get_repo.assert_called_once_with(session)
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.rename_file.assert_called_once_with(
            5, file_obj, "renamed.gcode"
        )

    def test_remove_file(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        file_obj = MagicMock(spec=File)

        FileService.remove_file(file_obj)

        get_repo.assert_called_once_with(session)
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.remove_file.assert_called_once_with(file_obj)

    def test_create_file_schedules_worker_tasks(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        created_file = MagicMock(spec=File)
        created_file.id = 10
        file_manager_cls.return_value.create_file.return_value = created_file

        worker = MagicMock()
        mocker.patch("desktop.services.fileService._get_worker_client", return_value=worker)

        result = FileService.create_file(1, "piece.gcode", "/tmp/piece.gcode")

        assert result == created_file
        get_repo.assert_called_once_with(session)
        file_manager_cls.assert_called_once_with(repository, ANY)
        file_manager_cls.return_value.create_file.assert_called_once_with(
            1, "piece.gcode", "/tmp/piece.gcode"
        )
        worker.generate_file_report.assert_called_once_with(10)
        worker.create_thumbnail.assert_called_once_with(10)

    def test_create_file_worker_failure_still_returns_file(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        file_manager_cls = mocker.patch("desktop.services.fileService.FileManager")
        created_file = MagicMock(spec=File)
        created_file.id = 10
        file_manager_cls.return_value.create_file.return_value = created_file

        worker = MagicMock()
        worker.generate_file_report.side_effect = RuntimeError("broker unavailable")
        mocker.patch("desktop.services.fileService._get_worker_client", return_value=worker)

        result = FileService.create_file(1, "piece.gcode", "/tmp/piece.gcode")

        assert result == created_file
        get_repo.assert_called_once_with(session)
        file_manager_cls.assert_called_once_with(repository, ANY)
        worker.generate_file_report.assert_called_once_with(10)
        worker.create_thumbnail.assert_not_called()
