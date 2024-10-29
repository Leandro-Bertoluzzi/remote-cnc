from desktop.components.CodeEditor import CodeEditor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestCodeEditor:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot):
        # Create an instance of CodeEditor
        self.code_editor = CodeEditor()
        qtbot.addWidget(self.code_editor)

    def test_code_editor_set_modified(self, qtbot: QtBot):
        # Wait for signal to trigger
        with qtbot.waitSignal(self.code_editor.textChanged, raising=True):
            self.code_editor.setPlainText('new text')

        # Assertions
        assert self.code_editor.modified

    def test_code_editor_get_modified(self, qtbot: QtBot):
        # Wait for signal to trigger
        with qtbot.waitSignal(self.code_editor.textChanged, raising=True):
            self.code_editor.setPlainText('new text')

        # Call method under test
        modified = self.code_editor.get_modified()

        # Assertions
        assert modified is True

    def test_code_editor_get_File_path(self):
        # Set widget attributes
        self.code_editor.file_path = 'path/to/file.gcode'

        # Call method under test
        file_path = self.code_editor.get_file_path()

        # Assertions
        assert file_path == 'path/to/file.gcode'

    @pytest.mark.parametrize(
            "modified,accept",
            [
                (False, False),
                (False, True),
                (True, False),
                (True, True)
            ]
        )
    def test_code_editor_new_file(self, mocker: MockerFixture, modified, accept):
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
    def test_code_editor_import_file(self, mocker: MockerFixture, modified, accept):
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
        self.code_editor.import_file()

        # Assertions
        should_update = not modified or accept
        assert mock_ask_to_save_changes.call_count == (1 if modified else 0)
        assert mock_select_file.call_count == (1 if should_update else 0)
        assert mocked_open.call_count == (1 if should_update else 0)
        assert mock_set_text.call_count == (1 if should_update else 0)
        if should_update:
            mocked_open.assert_called_with(file_path, "r")

    @pytest.mark.parametrize("file_path", ['', 'path/to/file.gcode'])
    @pytest.mark.parametrize("exported_as", [False, True])
    def test_code_editor_export_file(
        self,
        mocker: MockerFixture,
        file_path,
        exported_as
    ):
        # Mock attributes
        self.code_editor.file_path = file_path

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocked_open = mocker.patch('builtins.open', mocked_file_data)

        # Mock other methods
        mock_export_file_as = mocker.patch.object(
            CodeEditor,
            'export_file_as',
            return_value=exported_as
        )

        # Call method under test
        exported = self.code_editor.export_file()

        # Assertions
        assert exported == (not not file_path or exported_as)
        assert mock_export_file_as.call_count == (0 if file_path else 1)
        assert mocked_open.call_count == (1 if file_path else 0)
        if file_path:
            mocked_open.assert_called_with(file_path, "w")

    @pytest.mark.parametrize("file_path", ['', 'path/to/file.gcode'])
    def test_code_editor_export_file_as(self, mocker: MockerFixture, file_path):
        # Mock dialog methods
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
        exported = self.code_editor.export_file_as()

        # Assertions
        assert exported is (not not file_path)
        assert mock_select_file.call_count == 1
        assert mocked_open.call_count == (1 if file_path else 0)
        if file_path:
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
        mocker: MockerFixture,
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

    def test_code_editor_render_line_numbers(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock paint event handler
        mock_line_number_paint = mocker.patch.object(
            self.code_editor.indexArea,
            'update'
        )

        # Wait for signal to trigger
        with qtbot.waitSignal(self.code_editor.updateRequest, raising=True):
            self.code_editor.setPlainText(
                'Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10'
            )

        # Assertions
        assert mock_line_number_paint.call_count >= 1

    def test_code_editor_highlight_current_line(self, qtbot: QtBot):
        # Wait for signal to trigger
        with qtbot.waitSignal(self.code_editor.cursorPositionChanged, raising=True):
            self.code_editor.setPlainText('Line 1')
            self.code_editor.appendPlainText('Line 2')
            self.code_editor.appendPlainText('Line 3')

        # Move the cursor to the last line
        qtbot.keyClick(self.code_editor, Qt.Key.Key_Down)
        qtbot.keyClick(self.code_editor, Qt.Key.Key_Down)

        # Assertions
        highlighted_lines = self.code_editor.extraSelections().__len__()
        line_number = self.code_editor.extraSelections().pop().cursor.blockNumber() + 1
        assert highlighted_lines == 1
        assert line_number == 3
