from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Terminal import Terminal
from core.grbl.grblController import GrblController
import pytest
from views.ControlView import ControlView

class TestControlView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Create an instance of the parent
        self.parent = MainWindow()

        # Mock parent methods
        self.mock_add_toolbar = mocker.patch.object(MainWindow, 'addToolBar')
        self.mock_remove_toolbar = mocker.patch.object(MainWindow, 'removeToolBar')
        self.mock_back_to_menu = mocker.patch.object(MainWindow, 'backToMenu')

        # Create an instance of ControlView
        self.control_view = ControlView(parent=self.parent)
        qtbot.addWidget(self.control_view)

    def test_control_view_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.control_view.layout, MenuButton) == 1
        assert helpers.count_widgets_with_type(self.control_view.layout, ControllerActions) == 1
        assert helpers.count_widgets_with_type(self.control_view.layout, CodeEditor) == 1
        assert helpers.count_widgets_with_type(self.control_view.layout, ControllerStatus) == 1
        assert helpers.count_widgets_with_type(self.control_view.layout, Terminal) == 1

        # More assertions
        assert self.mock_add_toolbar.call_count == 1

    def test_control_view_goes_back_to_menu(self):
        # Call method under test
        self.control_view.backToMenu()

        # Assertions
        assert self.mock_remove_toolbar.call_count == 1
        assert self.mock_back_to_menu.call_count == 1

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

        # Mock methods
        mock_grbl_connect = mocker.patch.object(GrblController, 'connect')
        mock_grbl_disconnect = mocker.patch.object(GrblController, 'disconnect')

        # Call method under test
        self.control_view.connect_device()

        # Assertions
        should_connect = port and not connected
        should_disconnect = port and connected
        assert mock_grbl_connect.call_count == (1 if should_connect else 0)
        assert mock_grbl_disconnect.call_count == (1 if should_disconnect else 0)
        assert self.control_view.connect_button.text() == ('Desconectar' if should_connect else 'Conectar')
