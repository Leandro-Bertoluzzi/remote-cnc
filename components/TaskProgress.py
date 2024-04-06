from helpers.utils import applyStylesheet
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar, QFormLayout, QWidget
from typing import Optional

class TaskProgress(QWidget):
    def __init__(self, total_lines: Optional[int] = None, parent=None):
        super(TaskProgress, self).__init__(parent)

        self.sent_progress = QProgressBar(self)
        self.sent_progress.setAlignment(Qt.AlignCenter)
        self.process_progress = QProgressBar(self)
        self.process_progress.setAlignment(Qt.AlignCenter)

        self.sent_progress.setMinimum(0)
        self.process_progress.setMinimum(0)
        if total_lines:
            self.set_total(total_lines)
        self.set_progress(0, 0)

        layout = QFormLayout(self)
        layout.addRow('Enviado: ', self.sent_progress)
        layout.addRow('Procesado: ', self.process_progress)
        self.setLayout(layout)

        # Apply custom styles
        applyStylesheet(self, __file__, 'TaskProgress.qss')

    def set_total(self, total_lines: int):
        self.sent_progress.setMaximum(total_lines)
        self.process_progress.setMaximum(total_lines)

    def set_progress(self, sent_lines: int, processed_lines: int):
        self.sent_progress.setValue(sent_lines)
        self.process_progress.setValue(processed_lines)
