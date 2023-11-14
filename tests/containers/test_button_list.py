from containers.ButtonList import ButtonList
from PyQt5.QtWidgets import QPushButton

class TestButtonList:
    def test_button_list_init(self, qtbot, mocker, helpers):
        actions = [
            ('Action 1', mocker.Mock()),
            ('Action 2', mocker.Mock()),
            ('Action 3', mocker.Mock()),
            ('Action 4', mocker.Mock())
        ]
        button_list = ButtonList(actions)
        qtbot.addWidget(button_list)

        # Assertions
        assert helpers.count_widgets_with_type(button_list.layout(), QPushButton) == 4
