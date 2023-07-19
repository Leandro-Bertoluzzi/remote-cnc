import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from database.models.file import File
from views.FilesView import FilesView

class TestFileCard:
    file = File(user_id=1, file_name='example_file.gcode', file_path='path/example_file.gcode')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(FilesView, 'refreshLayout')

        self.parent = FilesView()
        self.file.id = 1
        self.card = FileCard(self.file, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_file_card_init(self, qtbot):
        assert self.card.file == self.file
        assert self.card.layout() is not None

    def test_file_card_update_file(self, qtbot, mocker):
        # Mock FileDataDialog methods
        mock_input = 'updated_name.gcode'
        mocker.patch.object(FileDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(FileDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_file = mocker.patch('components.cards.FileCard.updateFile')

        # Call the updateFile method
        self.card.updateFile()

        # Validate DB calls
        mock_update_file.call_count == 1
        update_file_params = {
            'id': 1,
            'user_id': 1,
            'file_name': 'updated_name.gcode',
            'file_name_saved': 'updated_name.gcode'
        }
        mock_update_file.assert_called_with(*update_file_params.values())

    def test_file_card_remove_file(self, qtbot, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_file = mocker.patch('components.cards.FileCard.removeFile')

        # Call the removeFile method
        self.card.removeFile()

        # Validate DB calls
        mock_remove_file.call_count == 1
