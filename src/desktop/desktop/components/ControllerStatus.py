from core.domain.cnc import Status
from core.domain.entities import Tool
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from desktop.helpers.utils import apply_stylesheet


class ControllerStatus(QWidget):
    DISCONNECTED = "DISCONNECTED"

    def __init__(self, parent=None):
        super(ControllerStatus, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        ############################################
        # 0      STATUS      |      TOOL           #
        # 1        X         |      FEED RATE      #
        # 1        Y         |      SPINDLE        #
        # 1        Z         |                     #
        ############################################

        # Widget structure and components definition
        layout_panel = QVBoxLayout()
        self.status = QLabel(ControllerStatus.DISCONNECTED)
        self.x_pos = QLabel("X: 0.0 (0.0)")
        self.y_pos = QLabel("Y: 0.0 (0.0)")
        self.z_pos = QLabel("Z: 0.0 (0.0)")

        layout_details = QVBoxLayout()
        self.tool = QLabel("Tool: ---")
        self.feedrate = QLabel("Feed rate: 0")
        self.spindle = QLabel("Spindle: 0")

        # Set 'class' dynamic property for styling
        self.status.setProperty("class", "status")
        self.x_pos.setProperty("class", "coordinates")
        self.y_pos.setProperty("class", "coordinates")
        self.z_pos.setProperty("class", "coordinates")

        for label in [self.status, self.x_pos, self.y_pos, self.z_pos]:
            layout_panel.addWidget(label)
        layout.addLayout(layout_panel)

        for label in [self.tool, self.feedrate, self.spindle]:
            layout_details.addWidget(label)
        layout.addLayout(layout_details)

        apply_stylesheet(self, __file__, "ControllerStatus.qss")

    def set_status(self, status: Status):
        self.status.setText(status["activeState"].upper())
        self.x_pos.setText(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos.setText(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos.setText(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool: Tool | None):
        if tool is None or tool.id is None:
            self.tool.setText("Tool: ---")
            return

        self.tool.setText(f"Tool: {tool.id} ({tool.name})")

    def set_feedrate(self, feedrate: float):
        self.feedrate.setText(f"Feed rate: {feedrate}")

    def set_spindle(self, spindle: float):
        self.spindle.setText(f"Spindle: {spindle}")
