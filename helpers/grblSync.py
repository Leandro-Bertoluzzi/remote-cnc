from core.grbl.grblController import GrblController
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from views.ControlView import ControlView   # pragma: no cover

# Constants
STATUS_POLL = 0.10  # seconds
COMMANDS_POLL = 0.10  # seconds


class Worker(QObject):
    new_message = pyqtSignal(str)
    new_status = pyqtSignal(dict, float, float, int)

    def __init__(self, grbl_controller: GrblController):
        super().__init__()
        self.grbl_controller = grbl_controller
        self._running = False

    def run(self):
        ts = tc = time.time()  # last time GRBL info was queried
        monitor = self.grbl_controller.grbl_monitor
        self._running = True

        while self._running:
            t = time.time()

            # Check for new commands?
            if t - tc > COMMANDS_POLL:
                message = monitor.getLog()
                if message:
                    # Emit new message signal
                    self.new_message.emit(message)
                tc = t

            # Refresh machine position?
            if t - ts > STATUS_POLL:
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
                ts = t

            time.sleep(0.1)

    def stop(self):
        self._running = False


class GrblSync:
    """Utility class to sync a GRBL device with the control view's widgets.
    It updates both the controller's status and the sent/received commands.
    """
    def __init__(self, control_view: 'ControlView'):
        # Attributes definition
        self.control_view = control_view
        self.grbl_controller: GrblController = control_view.grbl_controller

        # Thread configuration
        self.monitor_thread: Optional[QThread] = None
        self.monitor_worker = Worker(self.grbl_controller)

    def __del__(self):
        self.stop_monitor()

    def start_monitor(self):
        # Create a QThread object
        self.monitor_thread = QThread()
        # Move worker to the thread
        self.monitor_worker.moveToThread(self.monitor_thread)
        # Connect signals and slots
        self.monitor_thread.started.connect(self.monitor_worker.run)
        self.monitor_worker.new_message.connect(self.message_received)
        self.monitor_worker.new_status.connect(self.status_received)
        # Start the thread
        self.monitor_thread.start()

    def stop_monitor(self):
        if not self.monitor_thread:
            return
        self.monitor_worker.stop()

    def message_received(self, message: str):
        if message:
            self.control_view.write_to_terminal(message)

    def status_received(
            self,
            status: dict,
            feedrate: float,
            spindle: float,
            tool_index_grbl: int
    ):
        self.control_view.update_device_status(
            status,
            feedrate,
            spindle,
            tool_index_grbl
        )
