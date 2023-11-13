from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Terminal import Terminal
from core.utils.serial import SerialService
from views.ControlView import ControlView

class TestControlView:
    def test_control_view_init(self, qtbot, mocker, helpers):
        # Create an instance of ControlView
        parent = MainWindow()

        # Mock object methods
        mock_add_toolbar = mocker.patch.object(MainWindow, 'addToolBar')
        mock_get_ports = mocker.patch.object(SerialService, 'get_ports')

        # Create an instance of ControlView
        control_view = ControlView(parent)
        qtbot.addWidget(control_view)

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(control_view.layout, MenuButton) == 1
        assert helpers.count_widgets_with_type(control_view.layout, ControllerActions) == 1
        assert helpers.count_widgets_with_type(control_view.layout, CodeEditor) == 1
        assert helpers.count_widgets_with_type(control_view.layout, ControllerStatus) == 1
        assert helpers.count_widgets_with_type(control_view.layout, Terminal) == 1

        # More assertions
        assert mock_get_ports.call_count == 1
        assert mock_add_toolbar.call_count == 1

    def test_control_view_goes_back_to_menu(self, qtbot, mocker):
        # Create an instance of ControlView
        parent = MainWindow()

        # Mock parent methods
        mock_remove_toolbar = mocker.patch.object(MainWindow, 'removeToolBar')
        mock_back_to_menu = mocker.patch.object(MainWindow, 'backToMenu')

        # Create an instance of ControlView
        control_view = ControlView(parent)
        qtbot.addWidget(control_view)

        # Call method under test
        control_view.backToMenu()

        # Assertions
        assert mock_remove_toolbar.call_count == 1
        assert mock_back_to_menu.call_count == 1
