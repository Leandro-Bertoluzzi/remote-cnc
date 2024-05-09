from core.grbl.grblController import GrblController
from helpers.fileSender import FileSender
from logging import Logger
from PyQt5.QtCore import QTimer
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestFileSender:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Mock GRBL controller object
        self.grbl_controller = GrblController(Logger('test-logger'))

        # Create an instance of FileSender
        self.file_sender = FileSender(self.grbl_controller)

    def test_file_set_file_path(self):
        # Call method under test
        self.file_sender.set_file('/path/to/file.nc')

        # Assertions
        assert self.file_sender.file_path == '/path/to/file.nc'

    def test_file_sender_start(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_start = mocker.patch.object(QTimer, 'start')

        # Call method under test
        self.file_sender.start()

        # Assertions
        assert mock_timer_start.call_count == 1

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_pause(self, mocker: MockerFixture, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.pause()

        # Assertions
        assert self.file_sender._paused is True

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_resume(self, mocker: MockerFixture, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.resume()

        # Assertions
        assert self.file_sender._paused is False

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_toggle_paused(self, mocker: MockerFixture, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.toggle_paused()

        # Assertions
        assert self.file_sender._paused == (not paused)

    def test_file_sender_stop(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_stop = mocker.patch.object(QTimer, 'stop')

        # Call method under test
        self.file_sender.stop()

        # Assertions
        assert mock_timer_stop.call_count == 1

    @pytest.mark.parametrize("file_path", [None, 'path/to/file'])
    def test_file_sender_open_file(self, mocker: MockerFixture, file_path):
        # Mock attributes
        self.file_sender.file_path = file_path

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mock_open_file = mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender._open_file()

        # Assertions
        assert mock_open_file.call_count == (1 if file_path else 0)

    def test_file_sender_send_line(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_sender.sent_line, raising=True):
            self.file_sender._open_file()
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 1
        assert mock_grbl_send_command.call_count == 1

    def test_file_sender_no_file(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock GRBL methods
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_sender.sent_line, timeout=500, raising=False) as blocker:
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_send_command.call_count == 0
        # Check whether the signal was triggered
        assert blocker.signal_triggered is False

    def test_file_sender_paused(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)
        self.file_sender._open_file()

        # Mock state
        self.file_sender._paused = True

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_sender.sent_line, timeout=500, raising=False) as blocker:
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_send_command.call_count == 0
        # Check whether the signal was triggered
        assert blocker.signal_triggered is False

    def test_file_sender_avoids_filling_buffer(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            return_value=100.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_sender.sent_line, timeout=500, raising=False) as blocker:
            self.file_sender._open_file()
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 1
        assert mock_grbl_send_command.call_count == 0
        # Check whether the signal was triggered
        assert blocker.signal_triggered is False

    def test_file_sender_send_whole_file(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_path = 'path/to/file'

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Mock other methods
        mock_stop = mocker.patch.object(self.file_sender, 'stop')

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_sender.finished, raising=True):
            self.file_sender._open_file()
            self.file_sender.send_line()
            self.file_sender.send_line()
            self.file_sender.send_line()
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 4
        assert mock_grbl_send_command.call_count == 3
        assert mock_stop.call_count == 1
