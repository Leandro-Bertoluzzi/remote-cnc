from core.grbl.grblController import GrblController
import threading
import time
from typing import Optional

# Constants
STATUS_POLL = 0.25  # seconds
COMMANDS_POLL = 0.25  # seconds


class GrblSync:
    """Utility class to sync a GRBL device with the control view's widgets.
    It updates both the controller's status and the sent/received commands.
    """
    def __init__(self, control_view):
        # Attributes definition
        self.control_view = control_view
        self.grbl_controller: GrblController = control_view.grbl_controller
        self.monitor_thread: Optional[threading.Thread] = None

    def __del__(self):
        self.stop_monitor()

    def start_monitor(self):
        self.monitor_thread = threading.Thread(target=self.monitor_device)
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitor_thread = None

    def monitor_device(self):
        ts = tc = time.time()  # last time GRBL info was queried
        monitor = self.grbl_controller.grbl_monitor

        while self.monitor_thread:
            t = time.time()

            # Check for new commands?
            if t - tc > COMMANDS_POLL:
                message = monitor.getLog()
                if message:
                    self.control_view.write_to_terminal(message)
                tc = t

            # Refresh machine position?
            if t - ts > STATUS_POLL:
                status = self.grbl_controller.getStatusReport()
                feedrate = self.grbl_controller.getFeedrate()
                spindle = self.grbl_controller.getSpindle()
                tool_index_grbl = self.grbl_controller.getTool()
                self.control_view.update_device_status(
                    status,
                    feedrate,
                    spindle,
                    tool_index_grbl
                )
                ts = t

            time.sleep(0.1)
