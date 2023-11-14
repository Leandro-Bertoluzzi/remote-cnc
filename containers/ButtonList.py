from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from math import floor

class ButtonList(QWidget):
    def __init__(self, options=[], parent=None):
        super(ButtonList, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        for (label, action) in options:
            button = QPushButton(label)
            button.clicked.connect(action)
            layout.addWidget(button)
