from components.Terminal import Terminal
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit
import pytest
import threading


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

    def test_terminal_start_monitor(self, mocker):
        # Mock thread
        mock_thread_create = mocker.patch.object(threading.Thread, '__init__', return_value=None)
        mock_thread_start = mocker.patch.object(threading.Thread, 'start')

        # Call method under test
        self.terminal.start_monitor()

        # Assertions
        assert mock_thread_create.call_count == 1
        assert mock_thread_start.call_count == 1

    def test_terminal_stop_monitor(self):
        # Call method under test
        self.terminal.stop_monitor()

        # Assertions
        assert self.terminal.monitor_thread is None

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

    def test_terminal_monitor_status(self, mocker):
        # Mock attributes
        self.terminal.monitor_thread = threading.Thread()

        # Mock thread life cycle
        self.count = 0

        def manage_thread():
            self.count = self.count + 1
            if self.count == 3:
                self.terminal.monitor_thread = None
            return 'Test log'

        # Mock GRBL methods
        mock_grbl_get_log = mocker.Mock()
        mock_grbl_get_log.side_effect = manage_thread
        self.terminal.grbl_controller.grbl_monitor.getLog = mock_grbl_get_log

        # Call method under test
        self.terminal.monitor_messages()

        # Assertions
        assert mock_grbl_get_log.call_count == 3
        assert self.terminal.display_screen.toPlainText() == (
            'Test log\nTest log\nTest log\n'
        )
        assert self.terminal.monitor_thread is None
