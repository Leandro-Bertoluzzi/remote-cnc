from PyQt5.QtWidgets import QPlainTextEdit

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)

        # Apply custom styles
        self.setStyleSheet("background-color: 'white';")
