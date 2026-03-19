"""Tests for :class:`ControlView` — Gateway-based CNC control."""

import pytest
from core.utilities.gateway.constants import ACTION_PAUSE, ACTION_RESUME
from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.CodeEditor import CodeEditor
from desktop.components.ControllerStatus import ControllerStatus
from desktop.components.Terminal import Terminal
from desktop.containers.ControllerActions import ControllerActions
from desktop.helpers.gatewayMonitor import GatewayMonitor
from desktop.MainWindow import MainWindow
from desktop.services.deviceService import DeviceService
from desktop.views.ControlView import ControlView
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot

import tests.mocks.grbl as grbl_mocks

_FAKE_SESSION_ID = "abc123"


class TestControlView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        # Mock device service methods
        mocker.patch.object(DeviceService, "is_worker_busy", return_value=False)

        # Prevent real Redis connections from GatewayClient / GatewayMonitor
        self.mock_gateway = mocker.MagicMock()
        self.mock_sync = mocker.MagicMock(spec=GatewayMonitor)
        mocker.patch("desktop.views.ControlView.GatewayClient", return_value=self.mock_gateway)
        mocker.patch("desktop.views.ControlView.GatewayMonitor", return_value=self.mock_sync)

        # Create an instance of ControlView
        self.parent = mock_window
        self.control_view = ControlView(self.parent)
        qtbot.addWidget(self.control_view)

    # -- init ---------------------------------------------------------------

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_init(self, qtbot: QtBot, mocker: MockerFixture, helpers, device_busy):
        # Reset parent mocks call count
        self.parent.addToolBar.reset_mock()  # type: ignore[union-attr]

        # Mock device service methods
        mocker.patch.object(DeviceService, "is_worker_busy", return_value=device_busy)

        # Create an instance of ControlView
        control_view = ControlView(self.parent)
        qtbot.addWidget(control_view)

        # Validate amount of each type of widget
        layout = control_view.layout()
        assert helpers.count_grid_widgets(layout, MenuButton) == 1
        assert helpers.count_grid_widgets(layout, ControllerActions) == 1
        assert helpers.count_grid_widgets(layout, CodeEditor) == 1
        assert helpers.count_grid_widgets(layout, ControllerStatus) == (0 if device_busy else 1)
        assert helpers.count_grid_widgets(layout, Terminal) == 1

        # More assertions
        assert self.parent.addToolBar.call_count == (1 if device_busy else 2)  # type: ignore[union-attr]

    # -- navigation ---------------------------------------------------------

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_goes_back_to_menu(self, device_busy):
        self.control_view.device_busy = device_busy
        self.control_view.backToMenu()

        assert self.parent.removeToolBar.call_count == (1 if device_busy else 2)  # type: ignore[union-attr]
        self.parent.backToMenu.assert_called_once()  # type: ignore[attr-defined]

    def test_control_view_close_event(self, mocker: MockerFixture):
        mock_disconnect = mocker.patch.object(ControlView, "disconnect_device")
        self.control_view.closeEvent(QCloseEvent())
        assert mock_disconnect.call_count == 1

    # -- connect / disconnect -----------------------------------------------

    def test_connect_device_acquires_session(self):
        self.mock_gateway.acquire_session.return_value = _FAKE_SESSION_ID

        self.control_view.connect_device()

        assert self.control_view.connected is True
        assert self.control_view.session_id == _FAKE_SESSION_ID
        assert self.control_view.connect_button.text() == "Desconectar"
        self.mock_gateway.acquire_session.assert_called_once()
        self.mock_sync.start_monitor.assert_called_once()

    def test_connect_device_session_busy(self, mocker: MockerFixture):
        self.mock_gateway.acquire_session.return_value = None
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.control_view.connect_device()

        assert self.control_view.connected is False
        assert mock_popup.call_count == 1

    def test_connect_device_error(self, mocker: MockerFixture):
        self.mock_gateway.acquire_session.side_effect = Exception("connection refused")
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.control_view.connect_device()

        assert self.control_view.connected is False
        assert mock_popup.call_count == 1

    def test_disconnect_device_releases_session(self):
        # Pre-condition: connected
        self.control_view.connected = True
        self.control_view.session_id = _FAKE_SESSION_ID
        self.mock_gateway.release_session.return_value = True

        self.control_view.disconnect_device()

        assert self.control_view.connected is False
        assert self.control_view.session_id is None
        self.mock_gateway.release_session.assert_called_once_with(_FAKE_SESSION_ID)
        self.mock_sync.stop_monitor.assert_called_once()

    def test_disconnect_device_release_error(self, mocker: MockerFixture):
        self.control_view.connected = True
        self.control_view.session_id = _FAKE_SESSION_ID
        self.mock_gateway.release_session.side_effect = Exception("redis error")
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.control_view.disconnect_device()

        # Still connected because release raised
        assert self.control_view.connected is True
        assert mock_popup.call_count == 1

    def test_disconnect_device_runtime_error(self, mocker: MockerFixture):
        """The C++ widget may already be deleted if the window is closing."""
        self.control_view.connected = True
        self.control_view.session_id = _FAKE_SESSION_ID
        self.mock_gateway.release_session.return_value = True

        # Simulate C++ deletion
        self.control_view.connect_button.setText = mocker.Mock(
            side_effect=RuntimeError("wrapped C/C++ object deleted")
        )

        self.control_view.disconnect_device()

        assert self.control_view.connected is False
        self.mock_sync.stop_monitor.assert_called_once()

    def test_toggle_connected(self, mocker: MockerFixture):
        mock_connect = mocker.patch.object(ControlView, "connect_device")
        mock_disconnect = mocker.patch.object(ControlView, "disconnect_device")

        self.control_view.connected = False
        self.control_view.toggle_connected()
        assert mock_connect.call_count == 1

        self.control_view.connected = True
        self.control_view.toggle_connected()
        assert mock_disconnect.call_count == 1

    # -- heartbeat ----------------------------------------------------------

    def test_renew_session_success(self):
        self.control_view.session_id = _FAKE_SESSION_ID
        self.mock_gateway.renew_session.return_value = True

        self.control_view._renew_session()

        self.mock_gateway.renew_session.assert_called_once_with(_FAKE_SESSION_ID)

    def test_renew_session_failure_disconnects(self, mocker: MockerFixture):
        self.control_view.session_id = _FAKE_SESSION_ID
        self.control_view.connected = True
        self.mock_gateway.renew_session.return_value = False
        self.mock_gateway.release_session.return_value = True
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.control_view._renew_session()

        assert self.control_view.connected is False
        assert mock_popup.call_count == 1

    # -- GRBL actions -------------------------------------------------------

    def test_run_homing_cycle(self, mocker: MockerFixture):
        self.control_view.session_id = _FAKE_SESSION_ID
        mock_popup = mocker.patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok)

        self.control_view.run_homing_cycle()

        self.mock_gateway.send_command.assert_called_once_with(_FAKE_SESSION_ID, "$H")
        assert mock_popup.call_count == 1

    def test_disable_alarm(self):
        self.control_view.session_id = _FAKE_SESSION_ID

        self.control_view.disable_alarm()

        self.mock_gateway.send_command.assert_called_once_with(_FAKE_SESSION_ID, "$X")

    def test_toggle_check_mode(self, mocker: MockerFixture):
        self.control_view.session_id = _FAKE_SESSION_ID
        mock_popup = mocker.patch.object(QMessageBox, "information", return_value=QMessageBox.Ok)

        self.control_view.toggle_check_mode()

        self.mock_gateway.send_command.assert_called_once_with(_FAKE_SESSION_ID, "$C")
        assert mock_popup.call_count == 1

    def test_configure_grbl_shows_warning(self, mocker: MockerFixture):
        mock_popup = mocker.patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok)

        self.control_view.configure_grbl()

        assert mock_popup.call_count == 1

    # -- file execution -----------------------------------------------------

    @pytest.mark.parametrize("file_path", ["", "/path/to/file.gcode"])
    @pytest.mark.parametrize("modified", [False, True])
    def test_start_file_execution(self, mocker: MockerFixture, file_path, modified):
        self.control_view.session_id = _FAKE_SESSION_ID

        mock_get_file_path = mocker.patch.object(
            CodeEditor, "get_file_path", return_value=file_path
        )
        mock_get_modified = mocker.patch.object(CodeEditor, "get_modified", return_value=modified)
        mock_popup = mocker.patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok)

        self.control_view.start_file_execution()

        should_execute = not modified and file_path
        assert mock_get_file_path.call_count == 1
        assert mock_get_modified.call_count == (1 if file_path else 0)
        assert mock_popup.call_count == (1 if not should_execute else 0)
        assert self.mock_gateway.request_file_execution.call_count == (1 if should_execute else 0)
        if should_execute:
            self.mock_gateway.request_file_execution.assert_called_once_with(
                _FAKE_SESSION_ID, file_path
            )

    def test_toggle_pause(self):
        self.control_view.session_id = _FAKE_SESSION_ID

        # First toggle -> pause
        self.control_view.toggle_pause()
        self.mock_gateway.send_realtime.assert_called_with(_FAKE_SESSION_ID, ACTION_PAUSE)
        assert self.control_view._file_paused is True
        assert self.control_view.pause_button.text() == "Retomar"

        # Second toggle -> resume
        self.control_view.toggle_pause()
        self.mock_gateway.send_realtime.assert_called_with(_FAKE_SESSION_ID, ACTION_RESUME)
        assert self.control_view._file_paused is False
        assert self.control_view.pause_button.text() == "Pausar"

    def test_stop_file_execution(self):
        self.control_view.session_id = _FAKE_SESSION_ID

        self.control_view.stop_file_execution()

        self.mock_gateway.request_file_stop.assert_called_once_with(_FAKE_SESSION_ID)
        assert self.control_view.code_editor.isReadOnly() is False

    def test_finished_file_execution(self, mocker: MockerFixture):
        mock_popup = mocker.patch.object(QMessageBox, "information", return_value=QMessageBox.Ok)

        self.control_view.finished_file_execution()

        assert mock_popup.call_count == 1
        assert self.control_view.code_editor.isReadOnly() is False

    def test_failed_file_execution(self, mocker: MockerFixture):
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.control_view.failed_file_execution("GRBL alarm 2")

        assert mock_popup.call_count == 1

    # -- slots --------------------------------------------------------------

    def test_write_to_terminal(self, mocker: MockerFixture):
        mock_display = mocker.patch.object(Terminal, "display_text")

        self.control_view.write_to_terminal("some text")

        mock_display.assert_called_with("some text")

    def test_update_device_status(self, mocker: MockerFixture):
        mock_set_status = mocker.patch.object(ControllerStatus, "set_status")
        mock_set_feedrate = mocker.patch.object(ControllerStatus, "set_feedrate")
        mock_set_spindle = mocker.patch.object(ControllerStatus, "set_spindle")
        mock_set_tool = mocker.patch.object(ControllerStatus, "set_tool")

        self.control_view.update_device_status(grbl_mocks.grbl_status, grbl_mocks.grbl_parserstate)

        assert mock_set_status.call_count == 1
        assert mock_set_feedrate.call_count == 1
        assert mock_set_spindle.call_count == 1
        assert mock_set_tool.call_count == 1

    def test_update_file_progress(self, mocker: MockerFixture):
        mock_mark = mocker.patch.object(CodeEditor, "markProcessedLines")

        self.control_view.update_file_progress(42, 40, 100)

        mock_mark.assert_called_once_with(42)
