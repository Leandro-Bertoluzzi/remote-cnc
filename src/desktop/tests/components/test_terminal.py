import pytest
from desktop.components.Terminal import Terminal
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit


class TestTerminal:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Create an instance of Terminal (no longer needs GrblController)
        self.terminal = Terminal()
        qtbot.addWidget(self.terminal)

    def test_terminal_init(self, helpers):
        # Assertions
        assert helpers.count_widgets(self.terminal.layout(), QPlainTextEdit) == 1
        assert helpers.count_widgets(self.terminal.layout(), QLineEdit) == 1
        assert self.terminal.display_screen.toPlainText() == ""

    def test_terminal_display_text(self):
        # Call method under test
        self.terminal.display_text("some text")

        # Assertions
        assert self.terminal.display_screen.toPlainText() == "some text\n"

    def test_terminal_send_line_emits_signal(self, qtbot):
        # Mock state of widget
        self.terminal.input.setText("A G-code command")

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.terminal.command_submitted, raising=True) as blocker:
            self.terminal.send_line()

        # Assertions
        assert blocker.args == ["A G-code command"]
        assert self.terminal.input.text() == ""
        # Echoes the command to display
        assert "> A G-code command" in self.terminal.display_screen.toPlainText()
