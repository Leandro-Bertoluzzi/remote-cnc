from core.grbl.grblController import GrblController
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from views.ControlView import ControlView   # pragma: no cover

# Constants
SEND_INTERVAL = 0.10    # Seconds
MAX_BUFFER_FILL = 75    # Percentage


class Worker(QObject):
    finished = pyqtSignal()
    sent_line = pyqtSignal(int)

    def __init__(self, grbl_controller: GrblController):
        super().__init__()
        self.grbl_controller = grbl_controller
        self._running = False
        self._paused = False

    def run(self):
        if not self.file_path:
            return

        ts = time.time()  # last time a command was sent

        gcode = open(self.file_path, 'r')
        self._running = True
        current_line = 1

        while self._running:
            t = time.time()

            # Send new command?
            if t - ts > SEND_INTERVAL and not self._paused:
                # Try not to fill the GRBL buffer
                if self.grbl_controller.getBufferFill() > MAX_BUFFER_FILL:
                    continue

                line = gcode.readline()

                # EOF
                if not line:
                    gcode.close()
                    self.stop()
                    # Emit signal
                    self.finished.emit()
                    return

                self.grbl_controller.sendCommand(line)
                # Emit signal
                self.sent_line.emit(current_line)

                ts = t
                current_line += 1

        gcode.close()

    def set_file(self, file_path: str):
        self.file_path = file_path

    def stop(self):
        self._running = False

    def pause(self):
        if self._running:
            self._paused = True
            self.grbl_controller.setPaused(True)

    def resume(self):
        if self._running:
            self._paused = False
            self.grbl_controller.setPaused(False)

    def toggle_paused(self):
        if self._running:
            self._paused = not self._paused
            self.grbl_controller.setPaused(self._paused)


class FileSender:
    """Utility class to open a file and send it to the GRBL device, line by line.
    """
    def __init__(self, control_view: 'ControlView'):
        # Attributes definition
        self.control_view = control_view
        self.grbl_controller: GrblController = control_view.grbl_controller

        # Thread configuration
        self.file_thread: Optional[QThread] = None
        self.file_worker = Worker(self.grbl_controller)

    def __del__(self):
        self.stop()

    def set_file(self, file_path: str):
        self.file_worker.set_file(file_path)

    def start(self):
        # Create a QThread object
        self.file_thread = QThread()
        # Move worker to the thread
        self.file_worker.moveToThread(self.file_thread)
        # Connect signals and slots
        self.file_thread.started.connect(self.file_worker.run)
        self.file_worker.sent_line.connect(self.line_sent)
        self.file_worker.finished.connect(self.finished_stream)
        # Start the thread
        self.file_thread.start()

    def pause(self):
        self.file_worker.pause()

    def resume(self):
        self.file_worker.resume()

    def toggle_paused(self):
        self.file_worker.toggle_paused()

    def stop(self):
        if not self.file_thread:
            return
        self.file_worker.stop()
        self.file_thread.quit()
        self.file_thread.wait()

    def line_sent(self, line: int):
        self.control_view.update_already_read_lines(line)

    def finished_stream(self):
        self.control_view.finished_file_stream()
