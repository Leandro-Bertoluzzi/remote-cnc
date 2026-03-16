import pytest
from desktop.components.buttons.MainMenuButton import MainMenuButton
from desktop.MainWindow import MainWindow
from desktop.views.MainMenu import MainMenu
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMainMenu:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        # Create an instance of MainMenu
        self.parent = mock_window
        self.main_menu = MainMenu(parent=self.parent)
        qtbot.addWidget(self.main_menu)

    def test_main_menu_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets(self.main_menu.layout(), MainMenuButton) == 6

    def test_main_menu_redirects_to_view(self):
        # Call redirectToView method
        self.main_menu.redirectToView("Another view")

        # Validate amount of each type of widget
        assert self.parent.changeView.call_count == 1  # type: ignore[attr-defined]
