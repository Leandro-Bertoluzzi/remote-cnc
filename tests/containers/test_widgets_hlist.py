from containers.WidgetsHList import WidgetsHList
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton


class TestWidgetsHList:
    def test_widgets_hlist_init(self, qtbot, helpers):
        widgets = [
            QLabel('label 1'),
            QPushButton('button 1'),
            QLabel('label 2'),
            QPushButton('button 1'),
        ]
        widgets_list = WidgetsHList(widgets)
        qtbot.addWidget(widgets_list)

        # Assertions
        assert helpers.count_widgets(widgets_list.layout(), QWidget) == 4
        assert helpers.count_widgets(widgets_list.layout(), QLabel) == 2
        assert helpers.count_widgets(widgets_list.layout(), QPushButton) == 2
