import pytest
from core.domain.entities import File, User
from core.domain.exceptions import (
    DuplicatedFileError,
    DuplicatedFileNameError,
    EntityNotFoundError,
    FileSystemError,
    PersistenceError,
)
from desktop.config import settings
from desktop.presentation.components.buttons.MenuButton import MenuButton
from desktop.presentation.components.cards.FileCard import FileCard
from desktop.presentation.components.cards.MsgCard import MsgCard
from desktop.presentation.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.presentation.components.dialogs.FileDataDialog import FileDataDialog
from desktop.presentation.views.FilesView import FilesView
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestFilesView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_window):
        file_1 = File(user_id=1, file_name="example-file-1", file_hash="hashed-file-1")
        file_2 = File(user_id=1, file_name="example-file-2", file_hash="hashed-file-2")
        file_3 = File(user_id=1, file_name="example-file-3", file_hash="hashed-file-3")
        self.files_list = [file_1, file_2, file_3]

        self.user_test = User(
            name="test_user", email="test@email.com", password="password", role="admin"
        )
        for file in self.files_list:
            file.user = self.user_test

        self.parent = mock_window
        self.mock_file_service = mock_window._context.file_service
        self.mock_file_service.get_all_files.return_value = self.files_list
        mock_window._context.asset_service.get_assets.return_value = ([], [], [])

        self.files_view = FilesView(self.parent)
        qtbot.addWidget(self.files_view)

        self.mock_file_service.get_all_files.reset_mock()
        mock_window._context.asset_service.get_assets.reset_mock()

    def test_files_view_init(self, helpers):
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 3

    def test_files_view_init_with_no_files(self, helpers):
        self.mock_file_service.get_all_files.return_value = []
        files_view = FilesView(self.parent)

        assert helpers.count_widgets(files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(files_view.layout(), FileCard) == 0
        assert helpers.count_widgets(files_view.layout(), MsgCard) == 1

    def test_files_view_init_db_error(self, helpers):
        self.mock_file_service.get_all_files.side_effect = Exception("mocked-error")
        self.mock_file_service.get_all_files.return_value = None

        files_view = FilesView(self.parent)

        assert helpers.count_widgets(files_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(files_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(files_view.layout(), FileCard) == 0
        assert helpers.count_widgets(files_view.layout(), MsgCard) == 0

    def test_files_view_refresh_layout(self, helpers):
        self.files_list.pop()
        self.files_view.refreshLayout()

        assert self.mock_file_service.get_all_files.call_count == 1
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 2

    def test_files_view_refresh_layout_db_error(self, helpers):
        self.mock_file_service.get_all_files.side_effect = Exception("mocked-error")
        self.files_view.refreshLayout()

        assert self.mock_file_service.get_all_files.call_count == 1
        assert helpers.count_widgets(self.files_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 0

    def test_files_view_create_file(self, mocker: MockerFixture, helpers):
        mock_input = "example-file-4", "path/to/file.gcode"
        mocker.patch.object(FileDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, "getInputs", return_value=mock_input)

        def side_effect_create_file(user_id, name, origin_path):
            file_4 = File(user_id=1, file_name="example-file-4", file_hash="hash-for-new-file")
            file_4.user = self.user_test
            self.files_list.append(file_4)
            return file_4

        self.mock_file_service.create_file.side_effect = side_effect_create_file

        self.files_view.createFile()

        assert self.mock_file_service.create_file.call_count == 1
        assert self.mock_file_service.get_all_files.call_count == 1
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 4

    @pytest.mark.parametrize(
        "error, expected_error_level",
        [
            (DuplicatedFileNameError("mocked error"), "warning"),
            (DuplicatedFileError("mocked error"), "warning"),
            (FileSystemError("mocked error"), "critical"),
            (PersistenceError("mocked error"), "critical"),
        ],
    )
    def test_files_view_create_file_error(
        self, mocker: MockerFixture, helpers, error, expected_error_level
    ):
        mock_input = "example-file-3", "path/to/file.gcode"
        mocker.patch.object(FileDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, "getInputs", return_value=mock_input)
        self.mock_file_service.create_file.side_effect = error
        mock_popup = mocker.patch.object(
            QMessageBox, expected_error_level, return_value=QMessageBox.Ok
        )

        self.files_view.createFile()

        assert self.mock_file_service.create_file.call_count == 1
        assert mock_popup.call_count == 1
        assert self.mock_file_service.get_all_files.call_count == 0
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 3

    # Handler tests

    def test_files_view_on_file_rename_success(self, helpers):
        file = self.files_list[0]
        self.files_view.on_file_rename(file, "new_name.gcode")

        self.mock_file_service.rename_file.assert_called_once_with(
            settings.user_id, file, "new_name.gcode"
        )
        assert self.mock_file_service.get_all_files.call_count == 1

    @pytest.mark.parametrize(
        "error, expected_method",
        [
            (DuplicatedFileNameError("e"), "showWarning"),
            (FileSystemError("e"), "showError"),
            (PersistenceError("e"), "showError"),
            (EntityNotFoundError("e"), "showError"),
        ],
    )
    def test_files_view_on_file_rename_error(self, mocker: MockerFixture, error, expected_method):
        self.mock_file_service.rename_file.side_effect = error
        mock_popup = mocker.patch.object(self.files_view, expected_method)

        self.files_view.on_file_rename(self.files_list[0], "bad_name.gcode")

        assert mock_popup.call_count == 1
        assert self.mock_file_service.get_all_files.call_count == 0

    def test_files_view_on_file_remove_success(self, helpers):
        file = self.files_list[0]
        self.files_view.on_file_remove(file)

        self.mock_file_service.remove_file.assert_called_once_with(file)
        assert self.mock_file_service.get_all_files.call_count == 1

    def test_files_view_on_create_task_success(self):
        file = self.files_list[0]
        file.id = 1
        self.files_view.on_create_task(file, 2, 3, "task", "note")

        self.parent._context.task_service.create_task.assert_called_once_with(
            settings.user_id, 1, 2, 3, "task", "note"
        )

    def test_files_view_on_execute_task_success(self, qtbot: QtBot, mocker):
        file = self.files_list[0]
        file.id = 1
        self.parent._context.device_service.check_device_availability.return_value = None
        mocker.patch.object(self.files_view, "showInfo")

        with qtbot.waitSignal(self.files_view.task_dispatched, raising=True):
            self.files_view.on_execute_task(file, 2, 3, "task", "note")

        self.parent._context.task_service.create_and_execute_task.assert_called_once_with(
            settings.user_id, 1, 2, 3, "task", "note"
        )

    def test_files_view_on_execute_task_device_unavailable(self, mocker: MockerFixture):
        file = self.files_list[0]
        file.id = 1
        self.parent._context.device_service.check_device_availability.return_value = (
            "Dispositivo no disponible"
        )
        mock_error = mocker.patch.object(self.files_view, "showError")

        self.files_view.on_execute_task(file, 2, 3, "task", "note")

        assert mock_error.call_count == 1
        self.parent._context.task_service.create_and_execute_task.assert_not_called()
