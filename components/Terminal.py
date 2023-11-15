from core.grbl.grblController import GrblController
from core.utils.files import getFileNameInFolder
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
        self.window = QPlainTextEdit()
        self.window.setReadOnly(True)
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_line)

        layout.addWidget(self.window)
        layout.addWidget(self.input)

        # Apply custom styles
        stylesheet = getFileNameInFolder(__file__, 'Terminal.qss')
        with open(stylesheet,'r') as styles:
            self.setStyleSheet(styles.read())

    def display_text(self, text):
        self.window.insertPlainText(text)
        self.window.insertPlainText('\n')

    def send_line(self):
        line = self.input.text()
        self.input.clear()

        self.display_text(line)
        response = self.grbl_controller.streamLine(line)
        self.display_text(response['raw'])
