from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from core.utils.files import getFileNameInFolder


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
        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet, "r") as styles:
            self.setStyleSheet(styles.read())

    def setDescription(self, description: str) -> None:
        self.label_description.setText(description)

    def addButton(self, button: QPushButton) -> None:
        self.layout_buttons.addWidget(button)

    # Notifications

    def showWarning(self, title, text):
        QMessageBox.warning(self, title, text, QMessageBox.Ok)

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)
