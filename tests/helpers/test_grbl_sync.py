from helpers.grblSync import GrblSync, Worker
from PyQt5.QtCore import QThread
import pytest


class TestGrblSync:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        # Mock control view
        self.grbl_control_view = mocker.MagicMock()

        # Create an instance of Terminal
        self.grbl_sync = GrblSync(self.grbl_control_view)

    def test_grbl_sync_start_monitor(self, mocker):
        # Mock thread
        mock_worker_move_to_thread = mocker.patch.object(Worker, 'moveToThread')
        mock_thread_start = mocker.patch.object(QThread, 'start')

        # Call method under test
        self.grbl_sync.start_monitor()

        # Assertions
        assert mock_worker_move_to_thread.call_count == 1
        assert mock_thread_start.call_count == 1

    @pytest.mark.parametrize("running", [False, True])
    def test_grbl_sync_stop_monitor(self, mocker, running):
        # Mock attributes
        self.grbl_sync.monitor_thread = (QThread() if running else None)

        # Mock thread
        mock_worker_stop = mocker.patch.object(Worker, 'stop')

        # Call method under test
        self.grbl_sync.stop_monitor()

        # Assertions
        assert mock_worker_stop.call_count == (1 if running else 0)

    def test_grbl_sync_message_received(self, mocker):
        # Mock control view methods
        mock_control_view_terminal = mocker.patch.object(
            self.grbl_sync.control_view,
            'write_to_terminal'
        )

        # Call method under test
        self.grbl_sync.message_received('Testing')

        # Assertions
        assert mock_control_view_terminal.call_count == 1
        mock_control_view_terminal.assert_called_with('Testing')

    def test_grbl_sync_status_received(self, mocker):
        # Mock control view methods
        mock_control_view_update_status = mocker.patch.object(
            self.grbl_sync.control_view,
            'update_device_status'
        )

        # Call method under test
        self.grbl_sync.status_received({}, 50.0, 500.0, 1)

        # Assertions
        assert mock_control_view_update_status.call_count == 1
        mock_control_view_update_status.assert_called_with({}, 50.0, 500.0, 1)

    def test_grbl_sync_worker_stop(self):
        # Mock worker state
        self.grbl_sync.monitor_worker._running = True

        # Call method under test
        self.grbl_sync.monitor_worker.stop()

        # Assertions
        assert self.grbl_sync.monitor_worker._running is False

    def test_grbl_sync_monitor_status(self, qtbot, mocker):
        # Mock thread life cycle
        self.count = 0

        def manage_thread():
            self.count = self.count + 1
            if self.count == 3:
                self.grbl_sync.monitor_worker.stop()
            return 'Test log'

        # Mock GRBL methods
        grbl = self.grbl_sync.monitor_worker.grbl_controller
        mock_grbl_get_status = mocker.patch.object(grbl, 'getStatusReport', return_value={})
        mocker.patch.object(grbl, 'getFeedrate', return_value=50.0)
        mocker.patch.object(grbl, 'getSpindle', return_value=500.0)
        mocker.patch.object(grbl, 'getTool', return_value=1)
        mock_grbl_get_log = mocker.patch.object(
            grbl.grbl_monitor,
            'getLog',
            side_effect=manage_thread
        )

        # Call method under test
        with qtbot.waitSignals(
            [
                self.grbl_sync.monitor_worker.new_message,
                self.grbl_sync.monitor_worker.new_status
            ],
            raising=True
        ):
            self.grbl_sync.monitor_worker.run()

        # Assertions
        assert mock_grbl_get_status.call_count == 3
        assert mock_grbl_get_log.call_count == 3
        assert self.grbl_sync.monitor_worker._running is False
