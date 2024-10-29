from utilities.gcode.gcodeFileSender import GcodeFileSender, FinishedFile
from utilities.grbl.grblController import GrblController
from desktop.helpers.fileStreamer import FileStreamer
from logging import Logger
from PyQt5.QtCore import QTimer
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestFileStreamer:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Mock GRBL controller object
        self.grbl_controller = GrblController(Logger('test-logger'))

        # Create an instance of FileStreamer
        self.file_streamer = FileStreamer(self.grbl_controller)

    def test_file_set_file_path(self):
        # Call method under test
        self.file_streamer.set_file('/path/to/file.nc')

        # Assertions
        assert self.file_streamer.file_sender.file_path == '/path/to/file.nc'

    def test_file_streamer_start(self, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_sender_start = mocker.patch.object(GcodeFileSender, 'start')

        # Mock timer method
        mock_timer_start = mocker.patch.object(QTimer, 'start')

        # Call method under test
        self.file_streamer.start()

        # Assertions
        assert mock_sender_start.call_count == 1
        assert mock_timer_start.call_count == 1

    def test_file_streamer_pause(self, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_sender_pause = mocker.patch.object(GcodeFileSender, 'pause')

        # Call method under test
        self.file_streamer.pause()

        # Assertions
        assert mock_sender_pause.call_count == 1

    def test_file_streamer_resume(self, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_sender_resume = mocker.patch.object(GcodeFileSender, 'resume')

        # Call method under test
        self.file_streamer.resume()

        # Assertions
        assert mock_sender_resume.call_count == 1

    def test_file_streamer_toggle_paused(self, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_sender_toggle_paused = mocker.patch.object(GcodeFileSender, 'toggle_paused')

        # Call method under test
        self.file_streamer.toggle_paused()

        # Assertions
        assert mock_sender_toggle_paused.call_count == 1

    def test_file_streamer_stop(self, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_sender_stop = mocker.patch.object(GcodeFileSender, 'stop')

        # Mock timer method
        mock_timer_stop = mocker.patch.object(QTimer, 'stop')

        # Call method under test
        self.file_streamer.stop()

        # Assertions
        assert mock_timer_stop.call_count == 1
        assert mock_sender_stop.call_count == 1

    def test_file_streamer_send_line(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_send_line = mocker.patch.object(GcodeFileSender, 'send_line')

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_streamer.sent_line, raising=True):
            self.file_streamer.send_line()

        # Assertions
        assert mock_send_line.call_count == 1

    def test_file_streamer_send_whole_file(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock Gcode sender method
        mock_send_line = mocker.patch.object(
            GcodeFileSender,
            'send_line',
            side_effect=FinishedFile()
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.file_streamer.finished, raising=True):
            self.file_streamer.send_line()

        # Assertions
        assert mock_send_line.call_count == 1
