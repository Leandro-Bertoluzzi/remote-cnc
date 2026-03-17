from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from desktop.helpers.utils import applyStylesheet


class Terminal(QWidget):
    """Terminal widget for sending G-code commands.

    Emits :pyqt:`command_submitted(str)` when the user presses *Enter*.
    The parent view connects this signal to the appropriate sender
    (e.g. ``GatewayClient.send_command``).
    """

    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)
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
        applyStylesheet(self, __file__, "Terminal.qss")

    def display_text(self, text):
        self.display_screen.insertPlainText(text + "\n")

    def send_line(self):
        line = self.input.text()
        self.input.clear()

        self.command_submitted.emit(line)
        self.display_text(f"> {line}")
