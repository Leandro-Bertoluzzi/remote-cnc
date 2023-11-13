from PyQt5.QtWidgets import QPlainTextEdit

class Terminal(QPlainTextEdit):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)

        # Widget configuration
        self.setReadOnly(True)

        # Apply custom styles
        self.setStyleSheet("background-color: 'black'; color: 'brown'")
