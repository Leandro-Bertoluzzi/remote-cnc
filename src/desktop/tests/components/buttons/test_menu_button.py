from desktop.components.buttons.MenuButton import MenuButton
from PyQt5.QtWidgets import QWidget
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMenuButton:
    def test_menu_button_init(self, qtbot: QtBot):
        button = MenuButton('Test Button')
        qtbot.addWidget(button)

        assert button.text() == 'Test Button'
        assert button.isVisible() is False
        assert button.receivers(button.clicked) == 0

    def test_menu_button_on_click(self, qtbot, mocker):
        mock_on_click = mocker.Mock()

        button = MenuButton('Test Button', onClick=mock_on_click)
        qtbot.addWidget(button)
        button.click()

        assert mock_on_click.call_count == 1

    def test_menu_button_go_to_view(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock parent
        parent = QWidget()
        parent.redirectToView = mocker.Mock()

        # Instantiate button
        button = MenuButton('Test Button', goToView='Test view', parent=parent)
        qtbot.addWidget(button)

        # User interaction
        button.click()

        # Validate method call
        parent.redirectToView.assert_called_once()
