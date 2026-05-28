from typing import Callable

from desktop.helpers.utils import applyStylesheet
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class Card(QWidget):
    def __init__(self, parent=None):
        super(Card, self).__init__(parent)

        # Item description
        self.label_description = QLabel()

        # Layout for action buttons
        self.layout_buttons = QVBoxLayout()

        # Create and set layout
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.label_description)
        h_layout.addLayout(self.layout_buttons)
        h_layout.setAlignment(Qt.AlignLeft)

        layout = QVBoxLayout()
        layout.addLayout(h_layout)
        self.setLayout(layout)

        # Apply custom styles
        applyStylesheet(self, __file__, "Card.qss")

    def setDescription(self, description: str) -> None:
        self.label_description.setText(description)

    def addButton(self, text: str, callback: Callable, enabled: bool = True) -> None:
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setEnabled(enabled)
        self.layout_buttons.addWidget(button)
