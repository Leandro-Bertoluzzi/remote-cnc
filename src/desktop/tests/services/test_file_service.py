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

        mock_report = mocker.patch("desktop.services.fileService.generate_file_report")
        mock_thumb = mocker.patch("desktop.services.fileService.create_thumbnail")

        result = FileService.create_file(1, "test.gcode", "/tmp/test.gcode")

        assert result == mock_file
        mock_report.assert_called_once_with(10)
        mock_thumb.assert_called_once_with(10)

    def test_create_file_broker_failure_still_creates_file(self, mocker: MockerFixture):
        """If the broker is unavailable, the file should still be created."""
        mock_file = MagicMock(spec=File)
        mock_file.id = 10

        mocker.patch("desktop.services.fileService.get_db_session")
        mock_fm_class = mocker.patch("desktop.services.fileService.FileManager")
        mock_fm_class.return_value.create_file.return_value = mock_file

        # Simulate broker failure on report generation
        mocker.patch(
            "desktop.services.fileService.generate_file_report",
            side_effect=Exception("broker unavailable"),
        )
        mock_thumb = mocker.patch("desktop.services.fileService.create_thumbnail")

        # Should NOT raise — the exception is caught internally
        result = FileService.create_file(1, "test.gcode", "/tmp/test.gcode")

        # File is still returned
        assert result == mock_file
        # Thumbnail is NOT called because both calls share a single try block
        mock_thumb.assert_not_called()
