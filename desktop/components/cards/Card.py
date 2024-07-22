from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from helpers.utils import applyStylesheet
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow               # pragma: no cover
    from views.BaseListView import BaseListView     # pragma: no cover


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

    # Utilities

    def setDescription(self, description: str) -> None:
        self.label_description.setText(description)

    def addButton(
        self,
        text: str,
        callback: Callable,
        enabled: bool = True
    ) -> None:
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setEnabled(enabled)
        self.layout_buttons.addWidget(button)

    def getView(self) -> 'BaseListView':
        """Get the view containing this card.
        """
        return self.parent()  # type: ignore

    def getWindow(self) -> 'MainWindow':
        """Get the application's main window.
        """
        return self.parent().parent()  # type: ignore

    # Notifications

    def showInformation(self, title, text):
        self.getView().showInfo(title, text)

    def showWarning(self, title, text):
        self.getView().showWarning(title, text)

    def showError(self, title, text):
        self.getView().showError(title, text)
