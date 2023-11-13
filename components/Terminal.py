from PyQt5.QtWidgets import QTextEdit

class Terminal(QTextEdit):
    def __init__(self, parent=None):
        super(Terminal, self).__init__(parent)

        # Apply custom styles
        self.setStyleSheet("background-color: 'black'; color: 'brown'")
