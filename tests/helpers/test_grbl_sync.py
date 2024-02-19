from helpers.grblSync import GrblSync
import pytest
import threading


class TestGrblSync:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        # Mock control view
        self.grbl_control_view = mocker.MagicMock()

        # Create an instance of Terminal
        self.grbl_sync = GrblSync(self.grbl_control_view)

    def test_grbl_sync_start_monitor(self, mocker):
        # Mock thread
        mock_thread_create = mocker.patch.object(threading.Thread, '__init__', return_value=None)
        mock_thread_start = mocker.patch.object(threading.Thread, 'start')

        # Call method under test
        self.grbl_sync.start_monitor()

        # Assertions
        assert mock_thread_create.call_count == 1
        assert mock_thread_start.call_count == 1

    def test_grbl_sync_stop_monitor(self):
        # Call method under test
        self.grbl_sync.stop_monitor()

        # Assertions
        assert self.grbl_sync.monitor_thread is None

    def test_grbl_sync_monitor_status(self, mocker):
        # Mock attributes
        self.grbl_sync.monitor_thread = threading.Thread()

        # Mock thread life cycle
        self.count = 0

        def manage_thread():
            self.count = self.count + 1
            if self.count == 3:
                self.grbl_sync.monitor_thread = None
            return 'Test log'

        # Mock GRBL methods
        mock_grbl_get_status = mocker.patch.object(
            self.grbl_sync.grbl_controller,
            'getStatusReport'
        )
        mock_grbl_get_log = mocker.patch.object(
            self.grbl_sync.grbl_controller.grbl_monitor,
            'getLog',
            side_effect=manage_thread
        )

        # Mock control view methods
        mock_control_view_terminal = mocker.patch.object(
            self.grbl_sync.control_view,
            'write_to_terminal'
        )
        mock_control_view_update_status = mocker.patch.object(
            self.grbl_sync.control_view,
            'update_device_status'
        )

        # Call method under test
        self.grbl_sync.monitor_device()

        # Assertions
        assert mock_grbl_get_log.call_count == 3
        assert mock_grbl_get_status.call_count == 3
        assert mock_control_view_terminal.call_count == 3
        assert mock_control_view_update_status.call_count == 3
        assert self.grbl_sync.monitor_thread is None
