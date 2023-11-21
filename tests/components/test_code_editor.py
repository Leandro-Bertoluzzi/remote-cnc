from components.CodeEditor import CodeEditor
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import pytest


class TestCodeEditor:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        # Create an instance of CodeEditor
        self.code_editor = CodeEditor()
        qtbot.addWidget(self.code_editor)

    def test_code_editor_set_modified(self, qtbot):
        # Wait for signal to trigger
        with qtbot.waitSignal(self.code_editor.textChanged, raising=True):
            self.code_editor.setPlainText('new text')

        # Assertions
        assert self.code_editor.modified

    @pytest.mark.parametrize(
            "modified,accept",
            [
                (False, False),
                (False, True),
                (True, False),
                (True, True)
            ]
        )
    def test_code_editor_new_file(self, mocker, modified, accept):
        # Mock other methods
        mock_ask_to_save_changes = mocker.patch.object(
            CodeEditor,
            'ask_to_save_changes',
            return_value=accept
        )
        mock_set_text = mocker.patch.object(CodeEditor, 'setPlainText')

        # Conditions for test
        if modified:
            self.code_editor.set_modified()

        # Call method under test
        self.code_editor.new_file()

        # Assertions
        should_update = not modified or accept
        assert mock_ask_to_save_changes.call_count == (1 if modified else 0)
        assert mock_set_text.call_count == (1 if should_update else 0)

    @pytest.mark.parametrize(
            "modified,accept",
            [
                (False, False),
                (False, True),
                (True, False),
                (True, True)
            ]
        )
    def test_code_editor_open_file(self, mocker, modified, accept):
        # Mock dialog methods
        file_path = 'path/to/file.gcode'
        filters = 'G code files (*.txt *.gcode *.nc)'
        mock_select_file = mocker.patch.object(
            QFileDialog,
            'getOpenFileName',
            return_value=(file_path, filters)
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocked_open = mocker.patch('builtins.open', mocked_file_data)

        # Mock other methods
        mock_ask_to_save_changes = mocker.patch.object(
            CodeEditor,
            'ask_to_save_changes',
            return_value=accept
        )
        mock_set_text = mocker.patch.object(CodeEditor, 'setPlainText')

        # Conditions for test
        if modified:
            self.code_editor.set_modified()

        # Call method under test
        self.code_editor.open_file()

        # Assertions
        should_update = not modified or accept
        assert mock_ask_to_save_changes.call_count == (1 if modified else 0)
        assert mock_select_file.call_count == (1 if should_update else 0)
        assert mocked_open.call_count == (1 if should_update else 0)
        assert mock_set_text.call_count == (1 if should_update else 0)
        if should_update:
            mocked_open.assert_called_with(file_path, "r")

    @pytest.mark.parametrize("file_path", ['', 'path/to/file.gcode'])
    def test_code_editor_save_file(self, mocker, file_path):
        # Mock attributes
        self.code_editor.file_path = file_path

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocked_open = mocker.patch('builtins.open', mocked_file_data)

        # Mock other methods
        mock_save_file_as = mocker.patch.object(CodeEditor, 'save_file_as')

        # Call method under test
        self.code_editor.save_file()

        # Assertions
        assert mock_save_file_as.call_count == (0 if file_path else 1)
        assert mocked_open.call_count == (1 if file_path else 0)
        if file_path:
            mocked_open.assert_called_with(file_path, "w")

    def test_code_editor_save_file_as(self, mocker):
        # Mock dialog methods
        file_path = 'path/to/file.gcode'
        filters = 'G code files (*.txt *.gcode *.nc)'
        mock_select_file = mocker.patch.object(
            QFileDialog,
            'getSaveFileName',
            return_value=(file_path, filters)
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocked_open = mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.code_editor.save_file_as()

        # Assertions
        assert mock_select_file.call_count == 1
        assert mocked_open.call_count == 1
        mocked_open.assert_called_with(file_path, "w")

    @pytest.mark.parametrize(
            "msg_box_response,save_file_response,expected_result",
            [
                (QMessageBox.Yes, True, True),
                (QMessageBox.Yes, False, False),
                (QMessageBox.No, True, True),
                (QMessageBox.No, False, True),
                (QMessageBox.Cancel, True, False),
                (QMessageBox.Cancel, False, False)
            ]
        )
    def test_code_editor_ask_to_save_changes(
        self,
        mocker,
        msg_box_response,
        save_file_response,
        expected_result
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msg_box_response)

        # Mock other methods
        mock_save_file = mocker.patch.object(
            CodeEditor,
            'save_file',
            return_value=save_file_response
        )

        # Call the removeFile method
        result = self.code_editor.ask_to_save_changes()

        # Validate function calls
        assert mock_save_file.call_count == (1 if msg_box_response == QMessageBox.Yes else 0)
        assert result == expected_result
