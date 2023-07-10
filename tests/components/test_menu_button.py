from components.MenuButton import MenuButton
from views.MainMenu import MainMenu

class TestMenuButton:
    def test_menu_button_init(self, qtbot):
        button = MenuButton('Test Button')
        qtbot.addWidget(button)

        assert button.text() == 'Test Button'
        assert button.isVisible() is False
        assert button.receivers(button.clicked) == 0

    def test_menu_button_on_click(self, qtbot, mocker):
        mock_on_click = mocker.MagicMock()

        button = MenuButton('Test Button', onClick=mock_on_click)
        qtbot.addWidget(button)
        button.click()

        assert mock_on_click.call_count == 1

    def test_menu_button_go_to_view(self, qtbot, mocker):
        parent = MainMenu()
        button = MenuButton('Test Button', goToView='Test view', parent=parent)
        qtbot.addWidget(button)

        # Mock parent's method
        mock_main_menu_redirects_to_view = mocker.patch.object(MainMenu, 'redirectToView')

        # User interaction
        button.click()

        # Validate method call
        assert mock_main_menu_redirects_to_view.call_count == 1
