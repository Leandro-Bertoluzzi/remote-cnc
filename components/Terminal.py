from core.grbl.grblController import GrblController
from helpers.utils import applyStylesheet
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class Terminal(QWidget):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(Terminal, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.grbl_controller = grbl_controller

        # Widget configuration
        self.display_screen = QPlainTextEdit()
        self.display_screen.setReadOnly(True)
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_line)

        layout.addWidget(self.display_screen)
        layout.addWidget(self.input)

        # Apply custom styles
        applyStylesheet(self, __file__, 'Terminal.qss')

    def display_text(self, text):
        self.display_screen.insertPlainText(text + '\n')

    def send_line(self):
        line = self.input.text()
        self.input.clear()

        self.grbl_controller.sendCommand(line)
