from PyQt5.QtWidgets import QWidget, QHBoxLayout


class WidgetsHList(QWidget):
    def __init__(self, widgets: list[QWidget] = [], parent=None):
        super(WidgetsHList, self).__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        for widget in widgets:
            layout.addWidget(widget)
