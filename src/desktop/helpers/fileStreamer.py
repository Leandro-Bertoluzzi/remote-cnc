from utilities.gcode.gcodeFileSender import GcodeFileSender, FinishedFile
from utilities.grbl.grblController import GrblController
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Constants
SEND_INTERVAL = 100     # miliseconds


class FileStreamer(QObject):
    """Utility class to open a file and send it to the GRBL device, line by line.
    """
    # SIGNALS
    finished = pyqtSignal()
    sent_line = pyqtSignal(int)

    # CONSTRUCTOR

    def __init__(self, grbl_controller: GrblController):
        super().__init__()

        # Attributes definition
        self.file_sender = GcodeFileSender(grbl_controller, '')

        # Create and configure timers
        self.file_manager = QTimer(self)
        self.file_manager.setInterval(SEND_INTERVAL)
        self.file_manager.timeout.connect(self.send_line)

    # FLOW CONTROL

    def start(self):
        self.file_sender.start()
        self.file_manager.start()

    def is_paused(self) -> bool:
        return self.file_sender.is_paused()

    def pause(self):
        self.file_sender.pause()

    def resume(self):
        self.file_sender.resume()

    def toggle_paused(self):
        self.file_sender.toggle_paused()

    def stop(self):
        self.file_manager.stop()
        self.file_sender.stop()

    # UTILITIES

    def set_file(self, file_path: str):
        self.file_sender.set_file(file_path)

    # SLOTS

    def send_line(self):
        try:
            self.current_line = self.file_sender.send_line()
        except FinishedFile:
            self.stop()
            self.finished.emit()
            return

        self.sent_line.emit(self.current_line)
