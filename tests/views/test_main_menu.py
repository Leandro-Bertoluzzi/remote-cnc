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

    def test_main_menu_init(self):
        # Validate amount of each type of widget
        assert self.count_widgets_with_type(MenuButton) == 7

    def test_main_menu_redirects_to_view(self, mocker):
        # Mock parent's method
        mock_main_window_changes_view = mocker.patch.object(MainWindow, 'changeView')

        # Call redirectToView method
        self.main_menu.redirectToView("Another view")

        # Validate amount of each type of widget
        assert mock_main_window_changes_view.call_count == 1

    # Helper method
    def count_widgets_with_type(self, widgetType):
        count = 0
        for i in range(self.main_menu.layout().count()):
            widget = self.main_menu.layout().itemAt(i).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count
