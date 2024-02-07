from core.database.base import Session as SessionLocal
from core.database.repositories.toolRepository import ToolRepository
from core.grbl.grblController import GrblController
from core.utils.files import getFileNameInFolder
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import threading
import time
from typing import Optional

# Constants
STATUS_POLL = 0.25  # seconds


class ControllerStatus(QWidget):
    def __init__(
            self,
            grbl_controller: GrblController,
            parent=None
    ):
        super(ControllerStatus, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.tool_index = 0
        self.monitor_thread: Optional[threading.Thread] = None

        # Widget structure and components definition
        self.status = QLabel('DISCONNECTED')
        self.x_pos = QLabel('X: 0.0 (0.0)')
        self.y_pos = QLabel('Y: 0.0 (0.0)')
        self.z_pos = QLabel('Z: 0.0 (0.0)')
        self.tool = QLabel('Tool: xxx')
        self.feedrate = QLabel('Feed rate: 0')
        self.spindle = QLabel('Spindle: 0')

        # Set 'class' dynamic property for styling
        self.status.setProperty('class', 'status')
        self.x_pos.setProperty('class', 'coordinates')
        self.y_pos.setProperty('class', 'coordinates')
        self.z_pos.setProperty('class', 'coordinates')

        layout.addWidget(self.status)
        layout.addWidget(self.x_pos)
        layout.addWidget(self.y_pos)
        layout.addWidget(self.z_pos)
        layout.addWidget(self.tool)
        layout.addWidget(self.feedrate)
        layout.addWidget(self.spindle)

        stylesheet = getFileNameInFolder(__file__, 'ControllerStatus.qss')
        with open(stylesheet, 'r') as styles:
            self.setStyleSheet(styles.read())

    def __del__(self):
        self.stop_monitor()

    def start_monitor(self):
        self.monitor_thread = threading.Thread(target=self.update_status)
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitor_thread = None

    def set_status(self, status):
        self.status.setText(status['activeState'].upper())
        self.x_pos.setText(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos.setText(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos.setText(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool_number: int, tool_info):
        self.tool.setText(f'Tool: {tool_number} ({tool_info.name})')
        self.tool_index = tool_number

    def set_feedrate(self, feedrate: int):
        self.feedrate.setText(f'Feed rate: {feedrate}')

    def set_spindle(self, spindle: int):
        self.spindle.setText(f'Spindle: {spindle}')

    def update_status(self):
        tr = time.time()  # last time the status was queried

        while self.monitor_thread:
            t = time.time()

            # Refresh machine position?
            if t - tr < STATUS_POLL:
                time.sleep(0.01)
                continue

            tr = t
            status = self.grbl_controller.getStatusReport()
            self.set_status(status)

            feedrate = self.grbl_controller.getFeedrate()
            self.set_feedrate(feedrate)

            spindle = self.grbl_controller.getSpindle()
            self.set_spindle(spindle)

            tool_index_grbl = self.grbl_controller.getTool()
            if self.tool_index == tool_index_grbl:
                continue

            try:
                db_session = SessionLocal()
                repository = ToolRepository(db_session)
                tool_info = repository.get_tool_by_id(tool_index_grbl)
                self.set_tool(tool_index_grbl, tool_info)
            except Exception:
                pass
