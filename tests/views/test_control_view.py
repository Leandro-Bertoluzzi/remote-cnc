from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.dialogs.GrblConfigurationDialog import GrblConfigurationDialog
from components.Terminal import Terminal
from core.database.repositories.taskRepository import TaskRepository
from core.grbl.grblController import GrblController
from PyQt5.QtWidgets import QDialog, QMessageBox
import pytest
from views.ControlView import ControlView


class TestControlView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Create an instance of the parent
        self.parent = MainWindow()

        # Mock parent methods
        self.parent.addToolBar = mocker.Mock()
        self.parent.removeToolBar = mocker.Mock()
        self.parent.backToMenu = mocker.Mock()

        # Mock view methods
        mocker.patch.object(
            TaskRepository,
            'are_there_tasks_with_status',
            return_value=False
        )

        # Create an instance of ControlView
        self.control_view = ControlView(self.parent)
        qtbot.addWidget(self.control_view)

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_init(self, qtbot, mocker, helpers, device_busy):
        # Create an instance of the parent
        parent = MainWindow()

        # Mock parent methods
        parent.addToolBar = mocker.Mock()

        # Mock other functions
        mock_check_tasks_in_progress = mocker.patch.object(
            TaskRepository,
            'are_there_tasks_with_status',
            return_value=device_busy
        )

        # Create an instance of ControlView
        control_view = ControlView(parent)
        qtbot.addWidget(control_view)

        # Validate amount of each type of widget
        layout = control_view.layout
        assert helpers.count_widgets(layout, MenuButton) == 1
        assert helpers.count_widgets(layout, ControllerActions) == 1
        assert helpers.count_widgets(layout, CodeEditor) == 1
        assert helpers.count_widgets(layout, ControllerStatus) == (0 if device_busy else 1)
        assert helpers.count_widgets(layout, Terminal) == 1

        # More assertions
        assert parent.addToolBar.call_count == (1 if device_busy else 2)
        mock_check_tasks_in_progress.assert_called_once()

    def test_control_view_init_db_error(self, qtbot, mocker, helpers):
        # Create an instance of the parent
        parent = MainWindow()

        # Mock parent methods
        parent.addToolBar = mocker.Mock()

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
        layout = control_view.layout
        assert helpers.count_widgets(layout, MenuButton) == 1
        assert helpers.count_widgets(layout, ControllerActions) == 1
        assert helpers.count_widgets(layout, CodeEditor) == 1
        assert helpers.count_widgets(layout, ControllerStatus) == 0
        assert helpers.count_widgets(layout, Terminal) == 1

        # More assertions
        mock_popup.assert_called_once()
        assert parent.addToolBar.call_count == 1
        mock_check_tasks_in_progress.assert_called_once()

    @pytest.mark.parametrize("device_busy", [False, True])
    def test_control_view_goes_back_to_menu(self, device_busy):
        # Mock attributes
        self.control_view.device_busy = device_busy

        # Call method under test
        self.control_view.backToMenu()

        # Assertions
        assert self.parent.removeToolBar.call_count == (1 if device_busy else 2)
        self.parent.backToMenu.assert_called_once()

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
    def test_control_view_toggle_connected_device(self, mocker, port, connected):
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
        mock_start_status_monitor = mocker.patch.object(ControllerStatus, 'start_monitor')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')

        # Call method under test
        self.control_view.toggle_connected()

        # Assertions
        should_connect = port and not connected
        should_disconnect = connected
        assert mock_grbl_connect.call_count == (1 if should_connect else 0)
        assert mock_start_status_monitor.call_count == (1 if should_connect else 0)
        assert mock_write_to_terminal.call_count == (1 if should_connect else 0)
        assert mock_grbl_disconnect.call_count == (1 if should_disconnect else 0)
        connect_btn_text = self.control_view.connect_button.text()
        assert connect_btn_text == ('Desconectar' if should_connect else 'Conectar')
        if should_connect:
            mock_write_to_terminal.assert_called_with(grbl_init_message)

    def test_control_view_connect_device_serial_error(self, mocker):
        # Mock attributes
        self.control_view.port_selected = 'PORTx'
        self.control_view.connected = False

        # Mock methods
        mock_grbl_connect = mocker.patch.object(
            GrblController,
            'connect',
            side_effect=Exception('mocked-error')
        )
        mock_start_status_monitor = mocker.patch.object(ControllerStatus, 'start_monitor')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.toggle_connected()

        # Assertions
        assert mock_grbl_connect.call_count == 1
        assert mock_start_status_monitor.call_count == 0
        assert mock_write_to_terminal.call_count == 0
        assert self.control_view.connect_button.text() == 'Conectar'
        mock_popup.assert_called_once()

    def test_control_view_disconnect_device_serial_error(self, mocker):
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
        mock_start_status_monitor = mocker.patch.object(ControllerStatus, 'start_monitor')
        mock_stop_status_monitor = mocker.patch.object(ControllerStatus, 'stop_monitor')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.toggle_connected()

        # Assertions
        assert mock_start_status_monitor.call_count == 0
        assert mock_write_to_terminal.call_count == 0
        assert mock_grbl_disconnect.call_count == 1
        assert mock_stop_status_monitor.call_count == 0
        assert self.control_view.connect_button.text() == 'Desconectar'
        mock_popup.assert_called_once()

    @pytest.mark.parametrize(
        "show_in_terminal",
        [True, False]
    )
    def test_control_view_query_settings(self, mocker, show_in_terminal):
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
        mock_write_to_terminal = mocker.patch.object(
            ControlView,
            'write_to_terminal'
        )

        # Call method under test
        self.control_view.query_device_settings(show_in_terminal)

        # Assertions
        assert mock_grbl_query_settings.call_count == 1
        assert self.control_view.device_settings == grbl_settings
        assert mock_write_to_terminal.call_count == (2 if show_in_terminal else 0)

    def test_run_homing_cycle(self, mocker):
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

    def test_disable_alarm(self, mocker):
        # Mock methods
        mock_grbl_disable_alarm = mocker.patch.object(
            GrblController,
            'disableAlarm'
        )

        # Call method under test
        self.control_view.disable_alarm()

        # Assertions
        assert mock_grbl_disable_alarm.call_count == 1

    def test_toggle_check_mode(self, mocker):
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

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_configure_grbl(self, mocker, dialogResponse, expected_updated):
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

    def test_configure_grbl_no_changes(self, mocker):
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

    def test_control_view_write_to_terminal(self, mocker):
        # Mock methods
        mock_display_text = mocker.patch.object(Terminal, 'display_text')

        # Call method under test
        self.control_view.write_to_terminal('some text')

        # Assertions
        assert mock_display_text.call_count == 1
        mock_display_text.assert_called_with('some text')
