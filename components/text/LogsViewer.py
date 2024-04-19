from components.text.IndexedTextEdit import IndexedTextEdit
from config import GRBL_LOGS_FILE
from core.utils.logs import Log, LogsInterpreter, LogFileWatcher
import csv
import os
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QTextBlock
import shutil
import time
from typing import Optional

# Constants
LOGS_POLL = 0.10  # seconds


class Worker(QObject):
    new_log = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.watcher = LogFileWatcher(GRBL_LOGS_FILE)
        self._running = False
        self._paused = False

    def run(self):
        if not os.path.exists(GRBL_LOGS_FILE):
            return

        tc = time.time()  # last time GRBL info was queried
        self._running = True
        self.logs = self.watcher.watch()

        while self._running:
            if self._paused:
                continue

            t = time.time()

            # Check for new logs?
            if t - tc > LOGS_POLL:
                try:
                    log = next(self.logs)
                except StopIteration:
                    time.sleep(0.1)
                    continue
                else:
                    # Emit new message signal
                    self.new_log.emit(log)
                    tc = t

    def stop(self):
        self.watcher.stop_watching()
        self._running = False

    def pause(self):
        if self._running:
            self._paused = True

    def resume(self):
        if self._running:
            self._paused = False

    def toggle_paused(self):
        if self._running:
            self._paused = not self._paused


class LogsViewer(IndexedTextEdit):
    def __init__(self, parent=None):
        super(LogsViewer, self).__init__(parent)

        self.setReadOnly(True)
        self.setStyleSheet("background-color: 'white';")

        # Log file management
        self.logs = LogsInterpreter().interpret_file(
            GRBL_LOGS_FILE
        )

        # UI
        self.setup_ui()

        # Thread configuration
        self.logs_thread: Optional[QThread] = None
        self.logs_worker = Worker()

    def __del__(self):
        self.stop()

    # Thread control methods

    def pause(self):
        self.logs_worker.pause()

    def resume(self):
        self.logs_worker.resume()

    def toggle_paused(self):
        self.logs_worker.toggle_paused()

    def stop(self):
        if not self.logs_thread:
            return
        self.logs_worker.stop()
        self.logs_thread.quit()
        self.logs_thread.wait()

    def start_watching(self):
        # Create a QThread object
        self.logs_thread = QThread(self)
        # Move worker to the thread
        self.logs_worker.moveToThread(self.logs_thread)
        # Connect signals and slots
        self.logs_thread.started.connect(self.logs_worker.run)
        self.logs_worker.new_log.connect(self.add_log)
        # Start the thread
        self.logs_thread.start()

    # File system methods

    def export_logs(self, output_path: str):
        """Saves the current text to the selected file, or a new one.
        """
        if output_path.endswith('.csv'):
            with open(output_path, "w", newline='') as outfile:
                csv_writer = csv.writer(outfile, delimiter=";")
                csv_writer.writerow(["DATETIME", "LEVEL", "TYPE", "Message"])
                for log in self.logs:
                    csv_writer.writerow([log[0], log[1], log[2], log[3]])
            return

        # As a plain text file
        shutil.copy(GRBL_LOGS_FILE, output_path)

    # UI methods

    def setup_ui(self):
        for log in self.logs:
            message = log[-1]
            self.appendPlainText(message)

    def add_log(self, log: Log):
        self.logs.append(log)
        message = log[-1]
        self.appendPlainText(message)

    def indexAreaWidth(self):
        space = 3 + self.fontMetrics().width('99/99/9999 99:99:99')
        return space

    def setIndex(self, block: QTextBlock) -> str:
        line_number = block.blockNumber()
        if not self.logs:
            return ''
        time = self.logs[line_number][0]
        return time

    def setIndexPenColor(self, _) -> QColor:
        return QColor(Qt.black)
