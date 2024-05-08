from core.grbl.grblController import GrblController
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Constants
SEND_INTERVAL = 100     # miliseconds
MAX_BUFFER_FILL = 75    # Percentage


class FileSender(QObject):
    """Utility class to open a file and send it to the GRBL device, line by line.
    """
    # SIGNALS
    finished = pyqtSignal()
    sent_line = pyqtSignal(int)

    # CONSTRUCTOR

    def __init__(self, grbl_controller: GrblController):
        super().__init__()

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.file_path = ''
        self.gcode = None
        self._paused = False
        self.current_line = 1

        # Create and configure timers
        self.file_manager = QTimer(self)
        self.file_manager.setInterval(SEND_INTERVAL)
        self.file_manager.timeout.connect(self.send_line)

    def __del__(self):
        self.stop()

    # FLOW CONTROL

    def start(self):
        # Initialization
        self._open_file()
        # Start timer
        self.file_manager.start()

    def pause(self):
        self._paused = True
        self.grbl_controller.setPaused(True)

    def resume(self):
        self._paused = False
        self.grbl_controller.setPaused(False)

    def toggle_paused(self):
        self._paused = not self._paused
        self.grbl_controller.setPaused(self._paused)

    def stop(self):
        # Stop timer
        self.file_manager.stop()
        # Release resources
        self._close_file()

    # UTILITIES

    def set_file(self, file_path: str):
        self.file_path = file_path

    def _open_file(self):
        if not self.file_path:
            return

        self.gcode = open(self.file_path, 'r')
        self.current_line = 1

    def _close_file(self):
        if not self.gcode:
            return

        self.gcode.close()
        self._paused = False

    # SLOTS

    def send_line(self):
        if not self.gcode or self._paused:
            return

        # Try not to fill the GRBL buffer
        if self.grbl_controller.getBufferFill() > MAX_BUFFER_FILL:
            return

        line = self.gcode.readline()

        # EOF or end programm command
        if not line or (line.strip() in ['M2', 'M02', 'M30']):
            self.stop()
            # Emit signal
            self.finished.emit()
            return

        self.grbl_controller.sendCommand(line)
        # Emit signal
        self.sent_line.emit(self.current_line)

        self.current_line += 1
