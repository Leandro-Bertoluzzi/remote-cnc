from desktop.presentation.components.containers.ButtonList import ButtonList
from PyQt5.QtWidgets import QPushButton
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestButtonList:
    def test_button_list_init(self, qtbot: QtBot, mocker: MockerFixture, helpers):
        actions = [
            ("Action 1", mocker.Mock()),
            ("Action 2", mocker.Mock()),
            ("Action 3", mocker.Mock()),
            ("Action 4", mocker.Mock()),
        ]
        button_list = ButtonList(actions)
        qtbot.addWidget(button_list)

        # Assertions
        assert helpers.count_widgets(button_list.layout(), QPushButton) == 4
