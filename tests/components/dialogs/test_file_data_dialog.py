import pytest
from components.dialogs.FileDataDialog import FileDataDialog
from database.models.file import File

class TestFileDataDialog:
    fileInfo = File(user_id=1, file_name='example_file.gcode', file_path='path/example_file.gcode')

    def test_file_data_dialog_init(self, qtbot):
        dialog = FileDataDialog()
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("file_info", [None, fileInfo])
    def test_file_data_dialog_init_widgets(self, qtbot, file_info):
        dialog = FileDataDialog(fileInfo=file_info)
        qtbot.addWidget(dialog)

        expectedName = self.fileInfo.file_name if file_info is not None else ''
        expectedWindowTitle = 'Actualizar archivo' if file_info is not None else 'Subir archivo'

        assert dialog.name.text() == expectedName
        assert dialog.windowTitle() == expectedWindowTitle

    def test_file_data_dialog_get_inputs(self, qtbot):
        dialog = FileDataDialog(fileInfo=self.fileInfo)
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('updated_name.gcode')

        assert dialog.getInputs() == 'updated_name.gcode'
