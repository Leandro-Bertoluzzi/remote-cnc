from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Terminal import Terminal
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from core.grbl.grblController import GrblController
from PyQt5.QtWidgets import QMessageBox
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
        parent.addToolBar.assert_called_once()
        mock_check_tasks_in_progress.assert_called_once()

    def test_control_view_goes_back_to_menu(self):
        # Call method under test
        self.control_view.backToMenu()

        # Assertions
        self.parent.removeToolBar.assert_called_once()
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
    def test_control_view_connect_device(self, mocker, port, connected):
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
        mock_query_device_status = mocker.patch.object(ControlView, 'query_device_status')
        mock_write_to_terminal = mocker.patch.object(ControlView, 'write_to_terminal')

        # Call method under test
        self.control_view.connect_device()

        # Assertions
        should_connect = port and not connected
        should_disconnect = port and connected
        assert mock_grbl_connect.call_count == (1 if should_connect else 0)
        assert mock_query_device_status.call_count == (1 if should_connect else 0)
        assert mock_write_to_terminal.call_count == (1 if should_connect else 0)
        assert mock_grbl_disconnect.call_count == (1 if should_disconnect else 0)
        connect_btn_text = self.control_view.connect_button.text()
        assert connect_btn_text == ('Desconectar' if should_connect else 'Conectar')
        if should_connect:
            mock_write_to_terminal.assert_called_with(grbl_init_message)

    def test_control_view_query_status(self, mocker):
        grbl_status = {
            'activeState': 'idle',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        }

        # Mock methods
        mock_grbl_query_status = mocker.patch.object(
            GrblController,
            'queryStatusReport',
            return_value=grbl_status
        )
        mock_grbl_get_feedrate = mocker.patch.object(
            GrblController,
            'getFeedrate',
            return_value='500.0'
        )
        mock_grbl_get_spindle = mocker.patch.object(
            GrblController,
            'getSpindle',
            return_value='500.0'
        )
        mock_grbl_get_tool = mocker.patch.object(
            GrblController,
            'getTool',
            return_value='1'
        )
        mock_get_tool_by_id = mocker.patch.object(ToolRepository, 'get_tool_by_id')

        # Call method under test
        self.control_view.query_device_status()

        # Assertions
        assert mock_grbl_query_status.call_count == 1
        assert mock_grbl_get_feedrate.call_count == 1
        assert mock_grbl_get_spindle.call_count == 1
        assert mock_grbl_get_tool.call_count == 1
        assert mock_get_tool_by_id.call_count == 1

    def test_control_view_query_status_db_error(self, mocker):
        grbl_status = {
            'activeState': 'idle',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        }

        # Mock methods
        mocker.patch.object(GrblController, 'queryStatusReport', return_value=grbl_status)
        mocker.patch.object(GrblController, 'getFeedrate', return_value=500.0)
        mocker.patch.object(GrblController, 'getSpindle', return_value=500.0)
        mocker.patch.object(GrblController, 'getTool', return_value=1)
        mocker.patch.object(
            ToolRepository,
            'get_tool_by_id',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call method under test
        self.control_view.query_device_status()

        # Assertions
        assert mock_popup.call_count == 1

    def test_control_view_query_settings(self, mocker):
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
            'queryGrblSettings',
            return_value=grbl_settings
        )

        # Call method under test
        self.control_view.query_device_settings()

        # Assertions
        assert mock_grbl_query_settings.call_count == 1
        assert self.control_view.device_settings == grbl_settings

    def test_control_view_write_to_terminal(self, mocker):
        # Mock methods
        mock_display_text = mocker.patch.object(Terminal, 'display_text')

        # Call method under test
        self.control_view.write_to_terminal('some text')

        # Assertions
        assert mock_display_text.call_count == 1
        mock_display_text.assert_called_with('some text')
