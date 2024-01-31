import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from core.database.models import File, User
from core.database.repositories.fileRepository import DuplicatedFileNameError, FileRepository
from views.FilesView import FilesView


class TestFileCard:
    file = File(user_id=1, file_name='example_file.gcode', file_hash='hashed-file')

    user_test = User(
        name='test_user',
        email='test@email.com',
        password='password',
        role='admin'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(FilesView, 'refreshLayout')

        self.parent = FilesView()
        self.file.id = 1
        self.file.user = self.user_test
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
    def test_file_card_update_file(self, mocker, dialogResponse, expected_updated):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        mocker.patch.object(FileRepository, 'check_file_exists')
        mock_rename_file = mocker.patch('components.cards.FileCard.renameFile')
        mock_update_file = mocker.patch.object(FileRepository, 'update_file')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == (1 if expected_updated else 0)
        assert mock_update_file.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_file_params = {
                'id': 1,
                'user_id': 1,
                'file_name': 'updated_name.gcode'
            }
            mock_update_file.assert_called_with(*update_file_params.values())

    def test_file_card_update_file_no_change(self, mocker):
        # Mock FileDataDialog methods
        mock_input = 'example_file.gcode', 'path/to/example_file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        mock_rename_file = mocker.patch('components.cards.FileCard.renameFile')
        mock_update_file = mocker.patch.object(FileRepository, 'update_file')

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 0
        assert mock_update_file.call_count == 0

    def test_file_card_update_file_repeated_name(self, mocker):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        mocker.patch.object(
            FileRepository,
            'check_file_exists',
            side_effect=DuplicatedFileNameError('mocked error')
        )
        mock_rename_file = mocker.patch('components.cards.FileCard.renameFile')
        mock_update_file = mocker.patch.object(FileRepository, 'update_file')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 0
        assert mock_update_file.call_count == 0
        assert mock_popup.call_count == 1

    def test_file_card_update_file_fs_error(self, mocker):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        mocker.patch.object(FileRepository, 'check_file_exists')
        mock_rename_file = mocker.patch(
            'components.cards.FileCard.renameFile',
            side_effect=Exception('mocked error')
        )
        mock_update_file = mocker.patch.object(FileRepository, 'update_file')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 1
        assert mock_update_file.call_count == 0
        assert mock_popup.call_count == 1

    def test_file_card_update_file_db_error(self, mocker):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode', 'path/to/file.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock FS and DB methods
        mocker.patch.object(FileRepository, 'check_file_exists')
        mock_rename_file = mocker.patch('components.cards.FileCard.renameFile')
        mock_update_file = mocker.patch.object(
            FileRepository,
            'update_file',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateFile method
        self.card.updateFile()

        # Validate function calls
        assert mock_rename_file.call_count == 1
        assert mock_update_file.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_file_card_remove_file(self, mocker, msgBoxResponse, expectedMethodCalls):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock FS and DB methods
        mock_delete_file = mocker.patch('components.cards.FileCard.deleteFile')
        mock_remove_file = mocker.patch.object(FileRepository, 'remove_file')

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == expectedMethodCalls
        assert mock_remove_file.call_count == expectedMethodCalls

    def test_file_card_remove_file_fs_error(self, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock FS and DB methods
        mock_delete_file = mocker.patch(
            'components.cards.FileCard.deleteFile',
            side_effect=Exception('mocked error')
        )
        mock_remove_file = mocker.patch.object(FileRepository, 'remove_file')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == 1
        assert mock_remove_file.call_count == 0
        assert mock_popup.call_count == 1

    def test_file_card_remove_file_db_error(self, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock FS and DB methods
        mock_delete_file = mocker.patch('components.cards.FileCard.deleteFile')
        mock_remove_file = mocker.patch.object(
            FileRepository,
            'remove_file',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeFile method
        self.card.removeFile()

        # Validate function calls
        assert mock_delete_file.call_count == 1
        assert mock_remove_file.call_count == 1
        assert mock_popup.call_count == 1
