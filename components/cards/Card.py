from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from helpers.utils import applyStylesheet


class Card(QWidget):
    def __init__(self, parent=None):
        super(Card, self).__init__(parent)

        # Item description
        self.label_description = QLabel()

        # Layout for action buttons
        self.layout_buttons = QVBoxLayout()

        # Create and set layout
        layout = QHBoxLayout()
        layout.addWidget(self.label_description)
        layout.addLayout(self.layout_buttons)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        # Apply custom styles
        applyStylesheet(self, __file__, "Card.qss")

    def setDescription(self, description: str) -> None:
        self.label_description.setText(description)

    def addButton(self, button: QPushButton) -> None:
        self.layout_buttons.addWidget(button)

    # Notifications

    def showInformation(self, title, text):
        QMessageBox.information(self, title, text, QMessageBox.Ok)

    def showWarning(self, title, text):
        QMessageBox.warning(self, title, text, QMessageBox.Ok)

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)
