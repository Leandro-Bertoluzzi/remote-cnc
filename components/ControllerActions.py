from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import Qt

class ControllerActions(QTabWidget):
    def __init__(self, tabs=[], parent=None):
        super(ControllerActions, self).__init__(parent)

        for (widget, label) in tabs:
            self.addTab(widget, label)
