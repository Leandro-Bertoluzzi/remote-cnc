try:
    from ..grbl.grblController import GrblController
except ImportError:
    from grbl.grblController import GrblController

# Constants
MAX_BUFFER_FILL = 75    # Percentage


# Custom exceptions
class FinishedFile(Exception):
    pass


class GcodeFileSender:
    """Utility class to open a file and send it to the GRBL device, line by line.
    """
    # CONSTRUCTOR

    def __init__(self, grbl_controller: GrblController, file_path: str):
        # Attributes definition
        self.grbl_controller = grbl_controller
        self.file_path = file_path
        self.gcode = None
        self._paused = False
        self.current_line = 0

    def __del__(self):
        self._close_file()

    # FLOW CONTROL

    def start(self) -> int:
        return self._open_file()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def toggle_paused(self):
        self._paused = not self._paused

    def is_paused(self) -> bool:
        return self._paused

    def stop(self):
        self._close_file()

    # UTILITIES

    def set_file(self, file_path: str):
        self.file_path = file_path

    def _open_file(self) -> int:
        self.gcode = open(self.file_path, 'r')
        self.current_line = 0
        self._paused = False

        # Total amount of lines in file
        total_lines = len(self.gcode.readlines())

        # Reset file pointer to the beginning
        self.gcode.seek(0)

        return total_lines

    def _close_file(self):
        if not self.gcode:
            return

        self.gcode.close()
        self.gcode = None

    # SLOTS

    def send_line(self):
        if not self.gcode or self._paused:
            return

        # Try not to fill the GRBL buffer
        if self.grbl_controller.getBufferFill() > MAX_BUFFER_FILL:
            return

        line = self.gcode.readline()

        # EOF
        if not line:
            raise FinishedFile

        self.grbl_controller.sendCommand(line)

        # Return amount of sent lines so far
        self.current_line += 1
        return self.current_line
