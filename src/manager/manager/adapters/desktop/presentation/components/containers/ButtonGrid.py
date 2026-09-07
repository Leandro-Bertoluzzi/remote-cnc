import math
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QPushButton, QWidget

ButtonInfo = tuple[str, Callable[[], None]]


class ButtonGrid(QWidget):
    """Generates a grid 'as square as possible' for the given buttons."""

    def __init__(self, options: list[ButtonInfo], max_width=4, parent=None):
        super(ButtonGrid, self).__init__(parent)

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        amount = len(options)
        width = min(math.floor(math.sqrt(amount)), max_width)

        i = 0
        for label, action in options:
            x = math.floor(i / width)
            y = i - width * x
            button = QPushButton(label)
            button.clicked.connect(action)
            layout.addWidget(button, x, y)
            i = i + 1
