from PyQt5.QtWidgets import QTabWidget, QWidget

ActionInfo = tuple[QWidget, str]


class ControllerActions(QTabWidget):
    def __init__(self, tabs: list[ActionInfo], parent=None):
        super(ControllerActions, self).__init__(parent)

        for widget, label in tabs:
            self.addTab(widget, label)
