from components.Terminal import Terminal
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit
import pytest


class TestTerminal:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Create an instance of Terminal
        self.terminal = Terminal(self.grbl_controller)
        qtbot.addWidget(self.terminal)

    def test_terminal_init(self, helpers):
        # Assertions
        assert helpers.count_widgets(self.terminal.layout(), QPlainTextEdit) == 1
        assert helpers.count_widgets(self.terminal.layout(), QLineEdit) == 1
        assert self.terminal.display_screen.toPlainText() == ''

    def test_terminal_display_text(self):
        # Call method under test
        self.terminal.display_text('some text')

        # Assertions
        assert self.terminal.display_screen.toPlainText() == 'some text\n'

    def test_terminal_send_line(self):
        # Mock state of widget
        self.terminal.input.setText('A G-code command')

        # Call method under test
        self.terminal.send_line()

        # Assertions
        self.grbl_controller.sendCommand.assert_called_once()
        self.grbl_controller.sendCommand.assert_called_with('A G-code command')
        assert self.terminal.input.text() == ''
