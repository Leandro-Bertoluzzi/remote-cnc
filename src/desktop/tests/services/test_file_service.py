from unittest.mock import MagicMock

from core.database.models import File
from desktop.services.fileService import FileService
from pytest_mock.plugin import MockerFixture


class TestFileService:
    """Tests for FileService, especially broker-failure resilience in create_file."""

    def test_create_file_success(self, mocker: MockerFixture):
        mock_file = MagicMock(spec=File)
        mock_file.id = 10

        mocker.patch("desktop.services.fileService.get_db_session")
        mock_fm_class = mocker.patch("desktop.services.fileService.FileManager")
        mock_fm_class.return_value.create_file.return_value = mock_file

        mock_client = mocker.patch("desktop.services.fileService.WorkerClient")
        mock_client_instance = mock_client.return_value

        result = FileService.create_file(1, "test.gcode", "/tmp/test.gcode")

        assert result == mock_file
        mock_client_instance.generate_file_report.assert_called_once_with(10)
        mock_client_instance.create_thumbnail.assert_called_once_with(10)

    def test_create_file_broker_failure_still_creates_file(self, mocker: MockerFixture):
        """If the broker is unavailable, the file should still be created."""
        mock_file = MagicMock(spec=File)
        mock_file.id = 10

        mocker.patch("desktop.services.fileService.get_db_session")
        mock_fm_class = mocker.patch("desktop.services.fileService.FileManager")
        mock_fm_class.return_value.create_file.return_value = mock_file

        # Simulate broker failure when constructing WorkerClient or calling methods
        mock_client = mocker.patch("desktop.services.fileService.WorkerClient")
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_file_report.side_effect = Exception("broker unavailable")

        # Should NOT raise — the exception is caught internally
        result = FileService.create_file(1, "test.gcode", "/tmp/test.gcode")

        # File is still returned
        assert result == mock_file
        # Thumbnail is NOT called because both calls share a single try block
        mock_client_instance.create_thumbnail.assert_not_called()
