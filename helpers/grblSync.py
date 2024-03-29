from core.grbl.grblController import GrblController
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Constants
STATUS_POLL = 100      # miliseconds
COMMANDS_POLL = 100    # miliseconds


class GrblSync(QObject):
    """Utility class to sync a GRBL device with some widget via signals.
    """
    # SIGNALS

    new_message = pyqtSignal(str)
    new_status = pyqtSignal(object, float, float, int)

    # CONSTRUCTOR

    def __init__(self, grbl_controller: GrblController):
        super().__init__()

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.grbl_monitor = grbl_controller.grbl_monitor
        self._running = False

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
        # Start timers
        self.monitor_status.start()
        self.monitor_commands.start()

    def stop_monitor(self):
        # Stop timers
        self.monitor_status.stop()
        self.monitor_commands.stop()

    # SLOTS

    def get_status(self):
        status = self.grbl_controller.getStatusReport()
        feedrate = self.grbl_controller.getFeedrate()
        spindle = self.grbl_controller.getSpindle()
        tool_index_grbl = self.grbl_controller.getTool()

        # Emit new status signal
        self.new_status.emit(
            status,
            feedrate,
            spindle,
            tool_index_grbl
        )

    def get_command(self):
        message = self.grbl_monitor.getLog()
        if message:
            # Emit new message signal
            self.new_message.emit(message)
