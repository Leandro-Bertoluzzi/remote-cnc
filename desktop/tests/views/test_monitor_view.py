from components.buttons.MenuButton import MenuButton
from components.ControllerStatus import ControllerStatus
from components.text.LogsViewer import LogsViewer
from helpers.cncWorkerMonitor import CncWorkerMonitor
from MainWindow import MainWindow
from PyQt5.QtGui import QCloseEvent
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from views.MonitorView import MonitorView


class TestMonitorView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        # Mock worker monitor methods
        mocker.patch.object(CncWorkerMonitor, 'is_worker_running', return_value=False)

        # Mock logs monitor methods
        mocker.patch.object(LogsViewer, 'start')

        # Mock other methods
        mocker.patch.object(MonitorView, 'connect_worker')

        # Create an instance of MonitorView
        self.parent = mock_window
        self.monitor_view = MonitorView(self.parent)
        qtbot.addWidget(self.monitor_view)

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_monitor_view_init(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        helpers,
        device_busy
    ):
        # Reset parent mocks call count
        self.parent.addToolBar.reset_mock()

        # Mock worker monitor methods
        mock_check_tasks_in_progress = mocker.patch.object(
            CncWorkerMonitor,
            'is_worker_running',
            return_value=device_busy
        )

        # Create an instance of MonitorView
        monitor_view = MonitorView(self.parent)
        qtbot.addWidget(monitor_view)

        # Validate amount of each type of widget
        layout = monitor_view.layout()
        assert helpers.count_grid_widgets(layout, MenuButton) == 1
        assert helpers.count_grid_widgets(layout, LogsViewer) == 1
        assert helpers.count_grid_widgets(layout, ControllerStatus) == 1

        # More assertions
        assert monitor_view.status_monitor.isEnabled() == device_busy
        assert self.parent.addToolBar.call_count == 1
        assert mock_check_tasks_in_progress.call_count == 1

    def test_monitor_view_goes_back_to_menu(self):
        # Call method under test
        self.monitor_view.backToMenu()

        # Assertions
        self.parent.removeToolBar.call_count == 1
        self.parent.backToMenu.assert_called_once()

    def test_monitor_view_close_event(self, mocker: MockerFixture):
        # Mock methods
        mock_stop_logs_monitor = mocker.patch.object(LogsViewer, 'stop')

        # Call method under test
        self.monitor_view.closeEvent(QCloseEvent())

        # Assertions
        assert mock_stop_logs_monitor.call_count == 1

    def test_monitor_view_update_device_status(self, mocker: MockerFixture):
        # Mock methods
        mock_set_status = mocker.patch.object(ControllerStatus, 'set_status')
        mock_set_feedrate = mocker.patch.object(ControllerStatus, 'set_feedrate')
        mock_set_spindle = mocker.patch.object(ControllerStatus, 'set_spindle')
        mock_set_tool = mocker.patch.object(ControllerStatus, 'set_tool')

        # Call method under test
        self.monitor_view.update_device_status({}, 50.0, 500.0, 1)

        # Assertions
        assert mock_set_status.call_count == 1
        assert mock_set_feedrate.call_count == 1
        assert mock_set_spindle.call_count == 1
        assert mock_set_tool.call_count == 1

    def test_monitor_view_pause_logs(self, mocker: MockerFixture):
        # Mock methods
        mock_pause_logs_monitor = mocker.patch.object(LogsViewer, 'toggle_paused')

        # Call method under test
        self.monitor_view.pause_logs()

        # Assertions
        assert mock_pause_logs_monitor.call_count == 1
