import pytest
from PyQt5.QtWidgets import QFileDialog, QPushButton
from components.dialogs.FileDataDialog import FileDataDialog
from core.database.models import File


class TestFileDataDialog:
    fileInfo = File(
        user_id=1,
        file_name='example_file.gcode',
        file_hash='hashed-file'
    )

    def test_file_data_dialog_init(self, qtbot):
        dialog = FileDataDialog()
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("file_info", [None, fileInfo])
    def test_file_data_dialog_init_widgets(self, qtbot, helpers, file_info):
        dialog = FileDataDialog(fileInfo=file_info)
        qtbot.addWidget(dialog)

        expectedName = self.fileInfo.file_name if file_info is not None else ''
        expectedWindowTitle = 'Actualizar archivo' if file_info is not None else 'Subir archivo'
        expectedNameEnabled = True if file_info is not None else False
        expectedButtonBoxEnabled = True if file_info is not None else False
        buttonsCount = 0 if file_info is not None else 1

        assert dialog.name.text() == expectedName
        assert dialog.name.isEnabled() == expectedNameEnabled
        assert dialog.buttonBox.isEnabled() == expectedButtonBoxEnabled
        assert dialog.windowTitle() == expectedWindowTitle
        assert helpers.count_widgets(dialog.layout(), QPushButton) == buttonsCount

    def test_file_data_dialog_get_inputs_new_file(self, qtbot, mocker):
        dialog = FileDataDialog()
        qtbot.addWidget(dialog)

        file_path = 'path/to/file.gcode'
        filters = 'G code files (*.txt *.gcode *.nc)'
        mock_select_file = mocker.patch.object(
            QFileDialog,
            'getOpenFileName',
            return_value=(file_path, filters)
        )

        # Interaction with widget
        dialog.file.click()

        # Assertions
        assert dialog.name.isEnabled()
        assert dialog.buttonBox.isEnabled()
        assert dialog.getInputs() == ('file.gcode', 'path/to/file.gcode')

        # Interaction with widget
        dialog.name.setText('updated_name.gcode')

        # Assertions
        assert mock_select_file.call_count == 1
        assert dialog.getInputs() == ('updated_name.gcode', 'path/to/file.gcode')

    def test_file_data_dialog_get_inputs_existing_file(self, qtbot):
        dialog = FileDataDialog(fileInfo=self.fileInfo)
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('updated_name.gcode')

        assert dialog.getInputs() == ('updated_name.gcode', '')
