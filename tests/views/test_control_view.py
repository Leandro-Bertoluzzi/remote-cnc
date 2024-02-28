from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.dialogs.GrblConfigurationDialog import GrblConfigurationDialog
from components.Terminal import Terminal
from core.database.repositories.taskRepository import TaskRepository
from core.grbl.grblController import GrblController
from helpers.grblSync import GrblSync
from helpers.fileSender import FileSender
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from views.ControlView import ControlView


class TestControlView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture):
        # Create an instance of the parent
        self.parent = MainWindow()

        # Mock parent methods
        self.mock_add_toolbar = mocker.patch.object(MainWindow, 'addToolBar')
        self.mock_remove_toolbar = mocker.patch.object(MainWindow, 'removeToolBar')
        self.mock_back_to_menu = mocker.patch.object(MainWindow, 'backToMenu')

        # Mock DB methods
        mocker.patch.object(
            TaskRepository,
            'are_there_tasks_with_status',
            return_value=False
        )

        # Create an instance of ControlView
        self.control_view = ControlView(self.parent)
        qtbot.addWidget(self.control_view)

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_init(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        helpers,
        device_busy
    ):
        # Mock parent methods
        mock_add_toolbar = mocker.patch.object(MainWindow, 'addToolBar')

        # Mock DB methods
        mock_check_tasks_in_progress = mocker.patch.object(
            TaskRepository,
            'are_there_tasks_with_status',
            return_value=device_busy
        )

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
        assert mock_add_toolbar.call_count == (1 if device_busy else 2)
        assert mock_check_tasks_in_progress.call_count == 1

    def test_control_view_init_db_error(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        helpers
    ):
        # Create an instance of the parent
        parent = MainWindow()

        # Mock parent methods
        mock_add_toolbar = mocker.patch.object(MainWindow, 'addToolBar')

        # Mock other functions
        mock_check_tasks_in_progress = mocker.patch.object(
            TaskRepository,
            'are_there_tasks_with_status',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Create an instance of ControlView
        control_view = ControlView(parent)
        qtbot.addWidget(control_view)

        # Validate amount of each type of widget
        layout = control_view.layout()
        assert helpers.count_grid_widgets(layout, MenuButton) == 1
        assert helpers.count_grid_widgets(layout, ControllerActions) == 1
        assert helpers.count_grid_widgets(layout, CodeEditor) == 1
        assert helpers.count_grid_widgets(layout, ControllerStatus) == 0
        assert helpers.count_grid_widgets(layout, Terminal) == 1

        # More assertions
        mock_popup.assert_called_once()
        assert mock_add_toolbar.call_count == 1
        mock_check_tasks_in_progress.assert_called_once()

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_goes_back_to_menu(self, device_busy):
        # Mock attributes
        self.control_view.device_busy = device_busy

        # Call method under test
        self.control_view.backToMenu()

        # Assertions
        assert self.mock_remove_toolbar.call_count == (1 if device_busy else 2)
        self.mock_back_to_menu.assert_called_once()

    def test_control_view_close_event(self, mocker: MockerFixture):
        # Mock methods
        mock_disconnect = mocker.patch.object(ControlView, 'disconnect_device')

        # Call method under test
        self.control_view.closeEvent(QCloseEvent())

        # Assertions
        assert mock_disconnect.call_count == 1

    def test_control_view_set_selected_port(self):
        # Mock attributes
        self.control_view.port_selected = ''

        # Call method under test
        self.control_view.set_selected_port('PORTx')

        # Assertions
        assert self.control_view.port_selected == 'PORTx'

    @pytest.mark.parametrize(
        "port,connected",
        [
            ('', False),
            ('', True),
            ('PORTx', False),
            ('PORTx', True),
        ]
    )
    def test_control_view_toggle_connected_device(
        self,
        mocker: MockerFixture,
        port,
        connected
    ):
        # Mock attributes
        self.control_view.port_selected = port
        self.control_view.connected = connected

        grbl_init_message = 'Grbl 1.1h [\'$\' for help]'

        # Mock methods
        mock_grbl_connect = mocker.patch.object(
            GrblController,
            'connect',
            return_value={'raw': grbl_init_message}
        )
        mock_grbl_disconnect = mocker.patch.object(GrblController, 'disconnect')
        mock_start_monitor = mocker.patch.object(GrblSync, 'start_monitor')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')
        mock_stop_sending_file = mocker.patch.object(FileSender, 'stop')
        mock_stop_monitor = mocker.patch.object(GrblSync, 'stop_monitor')

        # Call method under test
        self.control_view.toggle_connected()

        # Assertions
        should_connect = port and not connected
        should_disconnect = connected
        assert mock_grbl_connect.call_count == (1 if should_connect else 0)
        assert mock_start_monitor.call_count == (1 if should_connect else 0)
        assert mock_write_to_terminal.call_count == (1 if should_connect else 0)
        assert mock_grbl_disconnect.call_count == (1 if should_disconnect else 0)
        assert mock_stop_sending_file.call_count == (1 if should_disconnect else 0)
        assert mock_stop_monitor.call_count == (1 if should_disconnect else 0)
        connect_btn_text = self.control_view.connect_button.text()
        assert connect_btn_text == ('Desconectar' if should_connect else 'Conectar')
        if should_connect:
            mock_write_to_terminal.assert_called_with(grbl_init_message)

    def test_control_view_connect_device_serial_error(self, mocker: MockerFixture):
        # Mock attributes
        self.control_view.port_selected = 'PORTx'
        self.control_view.connected = False

        # Mock methods
        mock_grbl_connect = mocker.patch.object(
            GrblController,
            'connect',
            side_effect=Exception('mocked-error')
        )
        mock_start_monitor = mocker.patch.object(GrblSync, 'start_monitor')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.connect_device()

        # Assertions
        assert mock_grbl_connect.call_count == 1
        assert mock_start_monitor.call_count == 0
        assert mock_write_to_terminal.call_count == 0
        assert self.control_view.connect_button.text() == 'Conectar'
        mock_popup.assert_called_once()

    def test_control_view_disconnect_device_serial_error(self, mocker: MockerFixture):
        # Mock attributes
        self.control_view.port_selected = 'PORTx'
        self.control_view.connected = True
        self.control_view.connect_button.setText('Desconectar')

        # Mock methods
        mock_grbl_disconnect = mocker.patch.object(
            GrblController,
            'disconnect',
            side_effect=Exception('mocked-error')
        )
        mock_stop_monitor = mocker.patch.object(GrblSync, 'stop_monitor')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.disconnect_device()

        # Assertions
        assert mock_grbl_disconnect.call_count == 1
        assert mock_stop_monitor.call_count == 0
        assert self.control_view.connect_button.text() == 'Desconectar'
        mock_popup.assert_called_once()

    def test_control_view_disconnect_device_runtime_error(self, mocker: MockerFixture):
        # Mock attributes
        self.control_view.connected = True

        # Mock exception
        self.control_view.connect_button.setText = mocker.Mock()
        self.control_view.connect_button.setText.side_effect = RuntimeError(
            'wrapped C/C++ object of type QToolButton has been deleted'
        )

        # Mock methods
        mock_grbl_disconnect = mocker.patch.object(GrblController, 'disconnect')
        mock_stop_monitor = mocker.patch.object(GrblSync, 'stop_monitor')
        mock_enable_serial_widgets = mocker.patch.object(ControlView, 'enable_serial_widgets')

        # Call method under test
        self.control_view.disconnect_device()

        # Assertions
        assert mock_grbl_disconnect.call_count == 1
        assert mock_stop_monitor.call_count == 1
        assert mock_enable_serial_widgets.call_count == 0

    def test_control_view_query_settings(self, mocker: MockerFixture):
        # Mock attributes
        self.control_view.device_settings = {}
        grbl_settings = {
            '$0': {
                'value': '10',
                'message': 'Step pulse time',
                'units': 'microseconds',
                'description': 'Sets time length per step. Minimum 3usec.'
            },
            '$1': {
                'value': '25',
                'message': 'Step idle delay',
                'units': 'milliseconds',
                'description': 'Sets a short hold delay when stopping ...'
            }
        }

        # Mock methods
        mock_grbl_query_settings = mocker.patch.object(
            GrblController,
            'getGrblSettings',
            return_value=grbl_settings
        )

        # Call method under test
        self.control_view.query_device_settings()

        # Assertions
        assert mock_grbl_query_settings.call_count == 1
        assert self.control_view.device_settings == grbl_settings

    def test_run_homing_cycle(self, mocker: MockerFixture):
        # Mock methods
        mock_grbl_home_cyle = mocker.patch.object(
            GrblController,
            'handleHomingCycle'
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.run_homing_cycle()

        # Assertions
        assert mock_grbl_home_cyle.call_count == 1
        assert mock_popup.call_count == 1

    def test_disable_alarm(self, mocker: MockerFixture):
        # Mock methods
        mock_grbl_disable_alarm = mocker.patch.object(
            GrblController,
            'disableAlarm'
        )

        # Call method under test
        self.control_view.disable_alarm()

        # Assertions
        assert mock_grbl_disable_alarm.call_count == 1

    def test_toggle_check_mode(self, mocker: MockerFixture):
        # Mock methods
        mock_grbl_toggle_checkmode = mocker.patch.object(
            GrblController,
            'toggleCheckMode'
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.toggle_check_mode()

        # Assertions
        assert mock_grbl_toggle_checkmode.call_count == 1
        assert self.control_view.checkmode
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize("file_path", ['', '/path/to/file.gcode'])
    @pytest.mark.parametrize("modified", [False, True])
    def test_start_file_stream(
        self,
        mocker: MockerFixture,
        file_path,
        modified
    ):
        # Mock code editor methods
        mock_get_file_path = mocker.patch.object(
            CodeEditor,
            'get_file_path',
            return_value=file_path
        )
        mock_get_file_modified = mocker.patch.object(
            CodeEditor,
            'get_modified',
            return_value=modified
        )

        # Mock file sender methods
        mock_set_file_to_stream = mocker.patch.object(FileSender, 'set_file')
        mock_resume_file_stream = mocker.patch.object(FileSender, 'resume')
        mock_start_file_stream = mocker.patch.object(FileSender, 'start')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.start_file_stream()

        # Assertions
        assert mock_get_file_path.call_count == 1
        assert mock_get_file_modified.call_count == (1 if file_path else 0)
        assert mock_popup.call_count == (1 if modified or not file_path else 0)
        assert mock_set_file_to_stream.call_count == (1 if not modified and file_path else 0)
        assert mock_resume_file_stream.call_count == (1 if not modified and file_path else 0)
        assert mock_start_file_stream.call_count == (1 if not modified and file_path else 0)

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_configure_grbl(
        self,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock methods
        mock_query_settings = mocker.patch.object(
            ControlView,
            'query_device_settings'
        )
        mock_grbl_set_settings = mocker.patch.object(
            GrblController,
            'setSettings'
        )

        # Mock GrblConfigurationDialog methods
        mocker.patch.object(GrblConfigurationDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(
            GrblConfigurationDialog,
            'getModifiedInputs',
            return_value={'$1': '5'}
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.configure_grbl()

        # Assertions
        assert mock_query_settings.call_count == 1
        assert mock_grbl_set_settings.call_count == (1 if expected_updated else 0)
        assert mock_popup.call_count == (1 if expected_updated else 0)

    def test_configure_grbl_no_changes(self, mocker: MockerFixture):
        # Mock methods
        mock_query_settings = mocker.patch.object(
            ControlView,
            'query_device_settings'
        )
        mock_grbl_set_settings = mocker.patch.object(
            GrblController,
            'setSettings'
        )

        # Mock GrblConfigurationDialog methods
        mocker.patch.object(GrblConfigurationDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(
            GrblConfigurationDialog,
            'getModifiedInputs',
            return_value={}
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.configure_grbl()

        # Assertions
        assert mock_query_settings.call_count == 1
        assert mock_grbl_set_settings.call_count == 0
        assert mock_popup.call_count == 0

    def test_control_view_write_to_terminal(self, mocker: MockerFixture):
        # Mock methods
        mock_display_text = mocker.patch.object(Terminal, 'display_text')

        # Call method under test
        self.control_view.write_to_terminal('some text')

        # Assertions
        assert mock_display_text.call_count == 1
        mock_display_text.assert_called_with('some text')

    def test_control_view_update_device_status(self, mocker: MockerFixture):
        # Mock methods
        mock_set_status = mocker.patch.object(ControllerStatus, 'set_status')
        mock_set_feedrate = mocker.patch.object(ControllerStatus, 'set_feedrate')
        mock_set_spindle = mocker.patch.object(ControllerStatus, 'set_spindle')
        mock_set_tool = mocker.patch.object(ControllerStatus, 'set_tool')

        # Call method under test
        self.control_view.update_device_status({}, 50.0, 500.0, 1)

        # Assertions
        assert mock_set_status.call_count == 1
        assert mock_set_feedrate.call_count == 1
        assert mock_set_spindle.call_count == 1
        assert mock_set_tool.call_count == 1
