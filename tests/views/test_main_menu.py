import pytest

from MainWindow import MainWindow
from components.MenuButton import MenuButton
from views.MainMenu import MainMenu

class TestMainMenu:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        self.parent = MainWindow()
        self.main_menu = MainMenu(parent=self.parent)
        qtbot.addWidget(self.main_menu)

    def test_main_menu_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.main_menu.layout(), MenuButton) == 7

    def test_main_menu_redirects_to_view(self, mocker):
        # Mock parent's method
        mock_main_window_changes_view = mocker.patch.object(MainWindow, 'changeView')

        # Call redirectToView method
        self.main_menu.redirectToView("Another view")

        # Validate amount of each type of widget
        assert mock_main_window_changes_view.call_count == 1
