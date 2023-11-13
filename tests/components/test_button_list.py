from components.ButtonList import ButtonList
from PyQt5.QtWidgets import QPushButton

class TestButtonList:
    def test_button_list_init(self, qtbot, helpers):
        actions = ['Action 1', 'Action 2', 'Action 3', 'Action 4']
        button_list = ButtonList(actions)
        qtbot.addWidget(button_list)

        # Assertions
        assert helpers.count_widgets_with_type(button_list.layout(), QPushButton) == 4
