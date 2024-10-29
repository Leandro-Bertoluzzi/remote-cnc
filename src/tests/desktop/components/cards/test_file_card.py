from desktop.components.cards.FileCard import FileCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from database.exceptions import DatabaseError
from database.models import File, User
from database.repositories.fileRepository import DuplicatedFileNameError
from utilities.fileManager import FileManager
from utilities.files import FileSystemError
from PyQt5.QtWidgets import QDialog, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestFileCard:
    file = File(user_id=1, file_name='example_file.gcode', file_hash='hashed-file')

    user_test = User(
        name='test_user',
        email='test@email.com',
        password='password',
        role='admin'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        # Update file
        self.file.id = 1
        self.file.user = self.user_test

        # Instantiate card
        self.parent = mock_view
        self.card = FileCard(self.file, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_file_card_init(self):
        description = self.card.label_description
        assert self.card.file == self.file
        assert description.text() == 'Archivo 1: example_file.gcode\nUsuario: test_user'
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_file_card_update_file(
        self,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_rename_file = mocker.patch.object(FileManager, 'rename_file')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == (1 if expected_updated else 0)

        if expected_updated:
            rename_file_params = {
                'user_id': 1,
                'file': self.file,
                'new_name': 'updated_name.gcode'
            }
            mock_rename_file.assert_called_with(*rename_file_params.values())

    def test_file_card_update_file_no_change(self, mocker: MockerFixture):
        # Mock FileDataDialog methods
        mock_input = 'example_file.gcode', 'path/to/example_file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_rename_file = mocker.patch.object(FileManager, 'rename_file')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 0

    def test_file_card_update_file_repeated_name(self, mocker: MockerFixture):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_rename_file = mocker.patch.object(
            FileManager,
            'rename_file',
            side_effect=DuplicatedFileNameError('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showWarning')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 1
        assert mock_popup.call_count == 1

    def test_file_card_update_file_fs_error(self, mocker: MockerFixture):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_rename_file = mocker.patch.object(
            FileManager,
            'rename_file',
            side_effect=FileSystemError('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 1
        assert mock_popup.call_count == 1

    def test_file_card_update_file_db_error(self, mocker: MockerFixture):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock file manager methods
        mock_rename_file = mocker.patch.object(
            FileManager,
            'rename_file',
            side_effect=DatabaseError('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expected_updated",
            [
                (QMessageBox.Yes, True),
                (QMessageBox.Cancel, False)
            ]
        )
    def test_file_card_remove_file(
        self,
        mocker: MockerFixture,
        msgBoxResponse,
        expected_updated
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock file manager methods
        mock_delete_file = mocker.patch.object(FileManager, 'remove_file')

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == (1 if expected_updated else 0)

    def test_file_card_remove_file_fs_error(self, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock file manager methods
        mock_delete_file = mocker.patch.object(
            FileManager,
            'remove_file',
            side_effect=FileSystemError('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == 1
        assert mock_popup.call_count == 1

    def test_file_card_remove_file_db_error(self, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock file manager methods
        mock_delete_file = mocker.patch.object(
            FileManager,
            'remove_file',
            side_effect=DatabaseError('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == 1
        assert mock_popup.call_count == 1
