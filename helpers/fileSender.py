from core.grbl.grblController import GrblController
import threading
import time
from typing import Optional

# Constants
SEND_INTERVAL = 0.10    # Seconds
MAX_BUFFER_FILL = 75    # Percentage


class FileSender:
    """Utility class to open a file and send it to the GRBL device, line by line.
    """
    def __init__(self, grbl_controller: GrblController):
        # Attributes definition
        self.grbl_controller = grbl_controller
        self.file_thread: Optional[threading.Thread] = None
        self.running = False
        self.paused = False
        self.file_path = ''

    def __del__(self):
        self.stop()

    def set_file(self, file_path: str):
        self.file_path = file_path

    def start(self):
        if self.running or not self.file_path:
            return
        self.file_thread = threading.Thread(target=self.send_commands)
        self.file_thread.start()
        self.running = True

    def pause(self):
        if not self.running:
            return
        self.grbl_controller.setPaused(True)
        self.paused = True

    def resume(self):
        if not self.running:
            return
        self.grbl_controller.setPaused(False)
        self.paused = False

    def toggle_paused(self):
        if not self.running:
            return
        self.paused = not self.paused
        self.grbl_controller.setPaused(self.paused)

    def stop(self):
        self.file_thread = None
        self.running = False

    def send_commands(self):
        ts = time.time()  # last time a command was sent

        gcode = open(self.file_path, 'r')

        while self.file_thread:
            t = time.time()

            # Send new command?
            if t - ts > SEND_INTERVAL and not self.paused:
                # Try not to fill the GRBL buffer
                if self.grbl_controller.getBufferFill() > MAX_BUFFER_FILL:
                    continue

                line = gcode.readline()

                # EOF
                if not line:
                    gcode.close()
                    self.stop()
                    return

                self.grbl_controller.sendCommand(line)
                ts = t

        gcode.close()
