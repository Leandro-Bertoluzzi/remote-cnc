from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.FileCard import FileCard
from desktop.components.cards.MsgCard import MsgCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from database.repositories.fileRepository import DatabaseError, DuplicatedFileError, \
    DuplicatedFileNameError, FileRepository
from utilities.fileManager import FileManager
from utilities.files import FileSystemError
from desktop.MainWindow import MainWindow
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from desktop.views.FilesView import FilesView
from database.models import File, User


class TestFilesView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        file_1 = File(user_id=1, file_name='example-file-1', file_hash='hashed-file-1')
        file_2 = File(user_id=1, file_name='example-file-2', file_hash='hashed-file-2')
        file_3 = File(user_id=1, file_name='example-file-3', file_hash='hashed-file-3')
        self.files_list = [file_1, file_2, file_3]

        self.user_test = User(
            name='test_user',
            email='test@email.com',
            password='password',
            role='admin'
        )

        for file in self.files_list:
            file.user = self.user_test

        # Patch the getAllFilesFromUser method with the mock function
        self.mock_get_all_files = mocker.patch.object(
            FileRepository,
            'get_all_files',
            return_value=self.files_list
        )

        # Create an instance of FilesView
        self.parent = mock_window
        self.files_view = FilesView(self.parent)
        qtbot.addWidget(self.files_view)

    def test_files_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_files.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 3

    def test_files_view_init_with_no_files(self, mocker: MockerFixture, helpers):
        mock_get_all_files = mocker.patch.object(
            FileRepository,
            'get_all_files',
            return_value=[]
        )
        files_view = FilesView(self.parent)
        # Validate DB calls
        mock_get_all_files.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(files_view.layout(), FileCard) == 0
        assert helpers.count_widgets(files_view.layout(), MsgCard) == 1

    def test_files_view_init_db_error(self, mocker: MockerFixture, helpers):
        mock_get_all_files = mocker.patch.object(
            FileRepository,
            'get_all_files',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Create test view
        files_view = FilesView(self.parent)

        # Assertions
        mock_get_all_files.assert_called_once()
        mock_popup.assert_called_once()
        assert helpers.count_widgets(files_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(files_view.layout(), FileCard) == 0
        assert helpers.count_widgets(files_view.layout(), MsgCard) == 0

    def test_files_view_refresh_layout(self, helpers):
        # We remove a file
        self.files_list.pop()

        # Call the refreshLayout method
        self.files_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_files.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 2

    def test_files_view_refresh_layout_db_error(self, mocker: MockerFixture, helpers):
        # Mock DB methods to simulate error(s)
        # 1st execution: Widget creation (needs to success)
        # 2nd execution: Test case
        mock_get_all_files = mocker.patch.object(
            FileRepository,
            'get_all_files',
            side_effect=[
                self.files_list,
                Exception('mocked-error')
            ]
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the method under test
        files_view = FilesView(self.parent)
        files_view.refreshLayout()

        # Assertions
        assert mock_get_all_files.call_count == 2
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(files_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(files_view.layout(), FileCard) == 0

    def test_files_view_create_file(self, mocker: MockerFixture, helpers):
        # Mock FileDataDialog methods
        mock_input = 'example-file-4', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        def side_effect_create_file(user_id, file_name, file_hash):
            file_4 = File(
                user_id=1,
                file_name='example-file-4',
                file_hash='hash-for-new-file'
            )
            file_4.user = self.user_test
            self.files_list.append(file_4)
            return 4

        mock_create_file = mocker.patch.object(
            FileManager,
            'create_file',
            side_effect=side_effect_create_file
        )

        # Mock call to worker
        mock_generate_report = mocker.patch('views.FilesView.generateFileReport.delay')
        mock_create_thumbnail = mocker.patch('views.FilesView.createThumbnail.delay')

        # Call the createFile method
        self.files_view.createFile()

        # Validate function calls
        assert mock_create_file.call_count == 1
        assert self.mock_get_all_files.call_count == 2
        assert mock_generate_report.call_count == 1
        assert mock_create_thumbnail.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 4

    @pytest.mark.parametrize("error, expected_error_level", [
        (DuplicatedFileNameError('mocked error'), 'warning'),
        (DuplicatedFileError('mocked error'), 'warning'),
        (FileSystemError('mocked error'), 'critical'),
        (DatabaseError('mocked error'), 'critical'),
    ])
    def test_files_view_create_file_repeated_name(
        self,
        mocker: MockerFixture,
        helpers,
        error: Exception,
        expected_error_level: str
    ):
        # Mock FileDataDialog methods
        mock_input = 'example-file-3', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_create_file = mocker.patch.object(
            FileManager,
            'create_file',
            side_effect=error
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(
            QMessageBox,
            expected_error_level,
            return_value=QMessageBox.Ok
        )

        # Mock call to worker
        mock_generate_report = mocker.patch('views.FilesView.generateFileReport.delay')
        mock_create_thumbnail = mocker.patch('views.FilesView.createThumbnail.delay')

        # Call the method under test
        self.files_view.createFile()

        # Assertions
        assert mock_create_file.call_count == 1
        assert mock_popup.call_count == 1
        assert self.mock_get_all_files.call_count == 1
        assert mock_generate_report.call_count == 0
        assert mock_create_thumbnail.call_count == 0
        assert helpers.count_widgets(self.files_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.files_view.layout(), FileCard) == 3
