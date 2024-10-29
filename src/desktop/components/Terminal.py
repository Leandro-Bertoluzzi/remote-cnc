from utilities.grbl.grblController import GrblController
from desktop.helpers.utils import applyStylesheet
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class Terminal(QWidget):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(Terminal, self).__init__(parent)
        self.grbl_controller = grbl_controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Widget configuration
        self.display_screen = QPlainTextEdit()
        self.display_screen.setReadOnly(True)
        layout.addWidget(self.display_screen)

        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_line)
        layout.addWidget(self.input)

        # Apply custom styles
        applyStylesheet(self, __file__, 'Terminal.qss')

    def display_text(self, text):
        self.display_screen.insertPlainText(text + '\n')

    def send_line(self):
        line = self.input.text()
        self.input.clear()

        self.grbl_controller.sendCommand(line)
