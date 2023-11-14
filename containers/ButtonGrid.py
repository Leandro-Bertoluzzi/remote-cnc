from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import Qt
from math import floor

class ButtonGrid(QWidget):
    def __init__(self, options=[], width=3, parent=None):
        super(ButtonGrid, self).__init__(parent)

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        i = 0
        for (label, action) in options:
            x = int(floor(i/width))
            y = int(i - width*x)
            button = QPushButton(label)
            button.clicked.connect(action)
            layout.addWidget(button, x, y)
            i = i+1
