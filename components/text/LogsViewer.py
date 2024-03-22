from components.text.IndexedTextEdit import IndexedTextEdit
from core.utils.logs import LogsInterpreter
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextBlock
from PyQt5.QtWidgets import QFileDialog


class LogsViewer(IndexedTextEdit):
    def __init__(self, parent=None):
        super(LogsViewer, self).__init__(parent)

        self.setReadOnly(True)
        self.setStyleSheet("background-color: 'white';")

        # Log file management
        self.logs = LogsInterpreter().interpret_file(
            Path.cwd() / Path('core', 'worker', 'grbl.log')
        )

        # UI
        self.setup_ui()

    # File system methods

    def export_logs(self):
        """Saves the current text to the selected file, or a new one.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar registro de actividad",
            "C:\\",
            "Log files (*.log *.csv *.txt)"
        )
        if file_path:
            content = self.toPlainText()
            with open(file_path, "w") as file:
                file.write(content)
                self.modified = False
            self.file_path = file_path

    # UI methods

    def setup_ui(self):
        for log in self.logs:
            message = log[-1]
            self.appendPlainText(message)

    def indexAreaWidth(self):
        space = 3 + self.fontMetrics().width('99/99/9999 99:99:99')
        return space

    def setIndex(self, block: QTextBlock) -> str:
        line_number = block.blockNumber()
        time = self.logs[line_number][0]
        return time

    def setIndexPenColor(self, _) -> QColor:
        return Qt.black
