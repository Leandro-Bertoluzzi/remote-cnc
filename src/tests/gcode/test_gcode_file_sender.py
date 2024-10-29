from utilities.grbl.grblController import GrblController
from utilities.gcode.gcodeFileSender import GcodeFileSender, FinishedFile
from io import BytesIO
from logging import Logger
import pytest
from pytest_mock.plugin import MockerFixture


class TestGcodeFileSender:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Mock GRBL controller object
        self.grbl_controller = GrblController(Logger('test-logger'))

        # Create an instance of GcodeFileSender
        self.file_sender = GcodeFileSender(self.grbl_controller, '/path/to/file')

    def test_file_set_file_path(self):
        # Call method under test
        self.file_sender.set_file('/path/to/file.nc')

        # Assertions
        assert self.file_sender.file_path == '/path/to/file.nc'

    def test_file_sender_start(self, mocker: MockerFixture):
        # Mock auxiliar method
        mock_open_file = mocker.patch.object(GcodeFileSender, '_open_file')

        # Call method under test
        self.file_sender.start()

        # Assertions
        assert mock_open_file.call_count == 1

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_pause(self, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.pause()

        # Assertions
        assert self.file_sender._paused is True

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_resume(self, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.resume()

        # Assertions
        assert self.file_sender._paused is False

    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_toggle_paused(self, paused):
        # Set attributes for test
        self.file_sender._paused = paused

        # Call method under test
        self.file_sender.toggle_paused()

        # Assertions
        assert self.file_sender._paused == (not paused)

    def test_file_sender_stop(self, mocker: MockerFixture):
        # Mock auxiliar method
        mock_close_file = mocker.patch.object(GcodeFileSender, '_close_file')

        # Call method under test
        self.file_sender.stop()

        # Assertions
        assert mock_close_file.call_count == 1

    def test_file_sender_open_file(self, mocker: MockerFixture):
        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mock_open_file = mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        lines = self.file_sender._open_file()

        # Assertions
        assert mock_open_file.call_count == 1
        assert lines == 3

    def test_file_sender_send_line(self, mocker: MockerFixture):
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

        # Mock file
        self.file_sender.gcode = BytesIO(b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')

        # Call method under test
        self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 1
        assert mock_grbl_send_command.call_count == 1

    def test_file_sender_no_file(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Call method under test
        self.file_sender.send_line()

        # Assertions
        assert mock_grbl_send_command.call_count == 0

    def test_file_sender_paused(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.grbl_controller,
            'sendCommand'
        )

        # Mock file
        self.file_sender.gcode = BytesIO(b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')

        # Mock state
        self.file_sender._paused = True

        # Call method under test
        self.file_sender.send_line()

        # Assertions
        assert mock_grbl_send_command.call_count == 0

    def test_file_sender_avoids_filling_buffer(self, mocker: MockerFixture):
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

        # Mock file
        self.file_sender.gcode = BytesIO(b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')

        # Call method under test
        self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 1
        assert mock_grbl_send_command.call_count == 0

    def test_file_sender_send_whole_file(self, mocker: MockerFixture):
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

        # Mock file
        self.file_sender.gcode = BytesIO(b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')

        # Call method under test and assert exception
        self.file_sender.send_line()
        self.file_sender.send_line()
        self.file_sender.send_line()
        with pytest.raises(FinishedFile):
            self.file_sender.send_line()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 4
        assert mock_grbl_send_command.call_count == 3
