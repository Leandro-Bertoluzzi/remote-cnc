from core.grbl.grblController import GrblController
from core.utils.files import getFileNameInFolder
from PyQt5.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import threading
import time
from typing import Optional

# Constants
QUEUE_POLL = 0.25  # seconds


class Terminal(QWidget):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(Terminal, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.monitor_thread: Optional[threading.Thread] = None

        # Widget configuration
        self.display_screen = QPlainTextEdit()
        self.display_screen.setReadOnly(True)
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_line)

        layout.addWidget(self.display_screen)
        layout.addWidget(self.input)

        # Apply custom styles
        stylesheet = getFileNameInFolder(__file__, 'Terminal.qss')
        with open(stylesheet, 'r') as styles:
            self.setStyleSheet(styles.read())

    def __del__(self):
        self.stop_monitor()

    def start_monitor(self):
        self.monitor_thread = threading.Thread(target=self.monitor_messages)
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitor_thread = None

    def display_text(self, text):
        self.display_screen.insertPlainText(text + '\n')

    def send_line(self):
        line = self.input.text()
        self.input.clear()

        self.grbl_controller.sendCommand(line)

    def monitor_messages(self):
        tr = time.time()  # last time the status was queried
        monitor = self.grbl_controller.grbl_monitor

        while self.monitor_thread:
            t = time.time()

            # Refresh machine position?
            if t - tr < QUEUE_POLL:
                time.sleep(0.1)
                continue

            tr = t

            message = monitor.getLog()

            if message:
                self.display_text(message)
