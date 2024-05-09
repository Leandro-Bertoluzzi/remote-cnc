from core.grbl.grblController import GrblController
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Constants
STATUS_POLL = 50       # miliseconds
COMMANDS_POLL = 100    # miliseconds


class GrblSync(QObject):
    """Utility class to sync a GRBL device with some widget via signals.
    """
    # SIGNALS

    new_message = pyqtSignal(str)
    new_status = pyqtSignal(object, object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    # CONSTRUCTOR

    def __init__(self, grbl_controller: GrblController):
        super().__init__()

        # Attributes definition
        self.grbl_status = grbl_controller.grbl_status
        self.grbl_monitor = grbl_controller.grbl_monitor
        self._has_error = False
        self._has_finished = False

        # Create and configure timers
        self.monitor_status = QTimer(self)
        self.monitor_status.setInterval(STATUS_POLL)
        self.monitor_status.timeout.connect(self.get_status)

        self.monitor_commands = QTimer(self)
        self.monitor_commands.setInterval(COMMANDS_POLL)
        self.monitor_commands.timeout.connect(self.get_command)

    def __del__(self):
        self.stop_monitor()

    # FLOW CONTROL

    def start_monitor(self):
        # Reset state
        self._has_error = False
        self._has_finished = False
        # Start timers
        self.monitor_status.start()
        self.monitor_commands.start()

    def stop_monitor(self):
        # Stop timers
        self.monitor_status.stop()
        self.monitor_commands.stop()

    # SLOTS

    def get_status(self):
        status = self.grbl_status.get_status_report()
        parserstate = self.grbl_status.get_parser_state()

        # Emit new status signal
        self.new_status.emit(
            status,
            parserstate
        )

        # Check error status
        if self.grbl_status.failed() and not self._has_error:
            error_message = self.grbl_status.get_error_message()
            self.failed.emit(error_message)
            self._has_error = True

        if self._has_error and not self.grbl_status.failed():
            self._has_error = False

        # Check if an "end of programm" command was sent
        if self.grbl_status.finished() and not self._has_finished:
            self.finished.emit()
            self._has_finished = True

    def get_command(self):
        message = self.grbl_monitor.getLog()
        if message:
            # Emit new message signal
            self.new_message.emit(message)
