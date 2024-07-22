from components.text.LogsViewer import LogsViewer, Worker
from core.utils.logs import LogsInterpreter, LogFileWatcher
from operator import xor
from PyQt5.QtCore import QThread
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestLogsViewer:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        # Mock the logs interpreter
        mocker.patch.object(
            LogsInterpreter,
            'interpret_file',
            return_value=[]
        )

        # Create an instance of Terminal
        self.logs_viewer = LogsViewer()

    def test_setup_ui(self, mocker: MockerFixture):
        # Mock the logs interpreter
        mocker.patch.object(
            LogsInterpreter,
            'interpret_file',
            return_value=[
                ('2023/12/12 00:00:00', 'INFO', None, 'Log 1'),
                ('2023/12/12 00:00:10', 'WARNING', None, 'Log 2'),
                ('2023/12/12 00:00:20', 'CRITICAL', None, 'Log 3'),
            ]
        )

        # Create an instance of Terminal
        logs_viewer = LogsViewer()

        # Assertions
        assert logs_viewer.toPlainText() == 'Log 1\nLog 2\nLog 3'

    def test_logs_viewer_start_watching(self, mocker: MockerFixture):
        # Mock thread
        mock_worker_move_to_thread = mocker.patch.object(Worker, 'moveToThread')
        mock_thread_start = mocker.patch.object(QThread, 'start')

        # Call method under test
        self.logs_viewer.start()

        # Assertions
        assert mock_worker_move_to_thread.call_count == 1
        assert mock_thread_start.call_count == 1

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_logs_viewer_pause(self, running, paused):
        # Mock worker status
        self.logs_viewer.logs_worker._running = running
        self.logs_viewer.logs_worker._paused = paused

        # Call method under test
        self.logs_viewer.pause()

        # Assertions
        """|Running | Paused | Result |
           | 0      | 0      |  0     |
           | 0      | 1      |  1     |
           | 1      | 0      |  1     |
           | 1      | 1      |  1     |
        """
        assert self.logs_viewer.logs_worker._paused == (running or paused)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_logs_viewer_resume(self, running, paused):
        # Mock thread
        self.logs_viewer.logs_worker._running = running
        self.logs_viewer.logs_worker._paused = paused

        # Call method under test
        self.logs_viewer.resume()

        # Assertions
        """|Running | Paused | Result |
           | 0      | 0      |  0     |
           | 0      | 1      |  1     |
           | 1      | 0      |  0     |
           | 1      | 1      |  0     |
        """
        assert self.logs_viewer.logs_worker._paused == (not running and paused)

    @pytest.mark.parametrize("running", [False, True])
    @pytest.mark.parametrize("paused", [False, True])
    def test_logs_viewer_toggle_paused(self, running, paused):
        # Mock thread
        self.logs_viewer.logs_worker._running = running
        self.logs_viewer.logs_worker._paused = paused

        # Call method under test
        self.logs_viewer.toggle_paused()

        # Assertions
        """|Running | Paused | Result |
           | 0      | 0      |  0     |
           | 0      | 1      |  1     |
           | 1      | 0      |  1     |
           | 1      | 1      |  0     |
        """
        assert self.logs_viewer.logs_worker._paused == xor(running, paused)

    @pytest.mark.parametrize("running", [False, True])
    def test_logs_viewer_stop_watching(self, mocker: MockerFixture, running):
        # Mock attributes
        self.logs_viewer.logs_thread = (QThread() if running else None)

        # Mock thread
        mock_worker_stop = mocker.patch.object(Worker, 'stop')
        mocker.patch.object(QThread, 'quit')
        mocker.patch.object(QThread, 'wait')

        # Call method under test
        self.logs_viewer.stop()

        # Assertions
        assert mock_worker_stop.call_count == (1 if running else 0)

    def test_logs_viewer_add_log(self, mocker: MockerFixture):
        # Mock ui methods
        mock_append_log_msg = mocker.patch.object(
            self.logs_viewer,
            'appendPlainText'
        )

        # Call method under test
        self.logs_viewer.add_log(
            ('2023/12/12 00:00:00', 'INFO', None, 'Testing')
        )

        # Assertions
        assert mock_append_log_msg.call_count == 1
        mock_append_log_msg.assert_called_with('Testing')

    def test_logs_viewer_worker_stop(self):
        # Mock worker state
        self.logs_viewer.logs_worker._running = True

        # Call method under test
        self.logs_viewer.logs_worker.stop()

        # Assertions
        assert self.logs_viewer.logs_worker._running is False

    def test_logs_viewer_watch_logs(self, qtbot: QtBot, mocker: MockerFixture):
        def manage_thread(_):
            self.logs_viewer.stop()

        # Mock file watcher
        mock_watcher = mocker.patch.object(
            LogFileWatcher,
            'watch',
            return_value=iter([
                ('2023/12/12 00:00:00', 'INFO', None, 'Log 1'),
                ('2023/12/12 00:00:10', 'WARNING', None, 'Log 2'),
                ('2023/12/12 00:00:20', 'CRITICAL', None, 'Log 3'),
            ])
        )
        mocker.patch('time.sleep', side_effect=manage_thread)

        # Mock thread methods
        mocker.patch.object(QThread, 'wait')

        # Call method under test
        with qtbot.waitSignals(
            [self.logs_viewer.logs_worker.new_log] * 3,
            raising=True
        ):
            self.logs_viewer.start()

        # Assertions
        assert mock_watcher.call_count == 1
        assert self.logs_viewer.logs_worker._running is False
        assert self.logs_viewer.toPlainText() == 'Log 1\nLog 2\nLog 3'
