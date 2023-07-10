from MainWindow import MainWindow
from views.MainMenu import MainMenu
from views.UsersView import UsersView

class TestMainWindow:
    def test_main_window_init(self, qtbot):
        window = MainWindow()
        qtbot.addWidget(window)

        assert type(window.centralWidget) is MainMenu
        assert window.windowTitle() == "CNC admin"

    def test_main_window_changes_view(self, qtbot, mocker):
        window = MainWindow()
        qtbot.addWidget(window)

        # Test changing view to 'users'
        mock_get_all_users = mocker.patch('views.UsersView.getAllUsers', return_value=[])

        window.changeView(UsersView)
        assert type(window.centralWidget) is UsersView

        # Test going back to the main menu
        window.backToMenu()
        assert type(window.centralWidget) is MainMenu
