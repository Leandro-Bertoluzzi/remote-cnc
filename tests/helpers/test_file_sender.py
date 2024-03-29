from helpers.fileSender import FileSender, Worker
from PyQt5.QtCore import QThread
import pytest
from pytest_mock.plugin import MockerFixture


class TestFileSender:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Create an instance of Terminal
        self.file_sender = FileSender(self.grbl_controller)

    def test_file_set_file_path(self):
        # Call method under test
        self.file_sender.set_file('/path/to/file.nc')

        # Assertions
        assert self.file_sender.file_worker.file_path == '/path/to/file.nc'

    def test_file_sender_start(self, mocker: MockerFixture):
        # Mock thread
        mock_worker_move_to_thread = mocker.patch.object(Worker, 'moveToThread')
        mock_thread_start = mocker.patch.object(QThread, 'start')

        # Call method under test
        self.file_sender.start()

        # Assertions
        assert mock_worker_move_to_thread.call_count == 1
        assert mock_thread_start.call_count == 1

    @pytest.mark.parametrize("running", [False, True])
    def test_file_sender_pause(self, mocker: MockerFixture, running):
        # Set attributes for test
        self.file_sender.file_worker._running = running

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.pause()

        # Assertions
        assert self.file_sender.file_worker._paused == running
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(True)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_resume(self, mocker: MockerFixture, running, paused):
        # Set attributes for test
        self.file_sender.file_worker._running = running
        self.file_sender.file_worker._paused = paused

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.resume()

        # Assertions
        assert self.file_sender.file_worker._paused == (True if paused and not running else False)
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(False)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_file_sender_toggle_paused(self, mocker: MockerFixture, running, paused):
        # Set attributes for test
        self.file_sender.file_worker._running = running
        self.file_sender.file_worker._paused = paused

        # Mock GRBL methods
        mock_grbl_pause = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'setPaused'
        )

        # Call method under test
        self.file_sender.toggle_paused()

        # Assertions
        # final_p = not(p) r + p not(r) = p xor r
        assert self.file_sender.file_worker._paused == (True if paused ^ running else False)
        assert mock_grbl_pause.call_count == (1 if running else 0)
        if running:
            mock_grbl_pause.assert_called_with(not paused)

    @pytest.mark.parametrize("running", [False, True])
    def test_file_sender_stop(self, mocker: MockerFixture, running):
        # Mock attributes
        self.file_sender.file_thread = (QThread() if running else None)

        # Mock thread
        mock_worker_stop = mocker.patch.object(Worker, 'stop')
        mocker.patch.object(QThread, 'quit')
        mocker.patch.object(QThread, 'wait')

        # Call method under test
        self.file_sender.stop()

        # Assertions
        assert mock_worker_stop.call_count == (1 if running else 0)

    def test_file_sender_send_whole_file(self, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.set_file('path/to/file')

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.file_worker.run()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 4
        assert mock_grbl_send_command.call_count == 3
        assert self.file_sender.file_worker._running is False

    def test_file_sender_avoids_filling_buffer(self, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_thread = QThread()
        self.file_sender.set_file('path/to/file')

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'getBufferFill',
            side_effect=[20.0, 20.0, 100.0, 100.0, 20.0, 20.0]
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'sendCommand'
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.file_worker.run()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 6
        assert mock_grbl_send_command.call_count == 3
        assert self.file_sender.file_worker._running is False

    def test_file_sender_thread_stopped(self, mocker: MockerFixture):
        # Mock attributes
        self.file_sender.file_thread = QThread()
        self.file_sender.set_file('path/to/file')

        # Mock thread life cycle
        self.count = 0

        def manage_thread(ignore: str):
            self.count = self.count + 1
            if self.count == 2:
                self.file_sender.stop()

        # Mock GRBL methods
        mock_grbl_get_buffer_fill = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'getBufferFill',
            return_value=10.0
        )
        mock_grbl_send_command = mocker.patch.object(
            self.file_sender.file_worker.grbl_controller,
            'sendCommand',
            side_effect=manage_thread
        )

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        self.file_sender.file_worker.run()

        # Assertions
        assert mock_grbl_get_buffer_fill.call_count == 2
        assert mock_grbl_send_command.call_count == 2
        assert self.file_sender.file_worker._running is False
