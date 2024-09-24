from core.database.base import SessionLocal
from core.database.repositories.toolRepository import ToolRepository
from core.grbl.types import Status
from helpers.utils import applyStylesheet
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class ControllerStatus(QWidget):
    DISCONNECTED = 'DISCONNECTED'

    def __init__(self, parent=None):
        super(ControllerStatus, self).__init__(parent)
        self.tool_index = 0
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
        self.x_pos = QLabel('X: 0.0 (0.0)')
        self.y_pos = QLabel('Y: 0.0 (0.0)')
        self.z_pos = QLabel('Z: 0.0 (0.0)')

        layout_details = QVBoxLayout()
        self.tool = QLabel('Tool: xxx')
        self.feedrate = QLabel('Feed rate: 0')
        self.spindle = QLabel('Spindle: 0')

        # Set 'class' dynamic property for styling
        self.status.setProperty('class', 'status')
        self.x_pos.setProperty('class', 'coordinates')
        self.y_pos.setProperty('class', 'coordinates')
        self.z_pos.setProperty('class', 'coordinates')

        for label in [
            self.status, self.x_pos, self.y_pos, self.z_pos
        ]:
            layout_panel.addWidget(label)
        layout.addLayout(layout_panel)

        for label in [
            self.tool, self.feedrate, self.spindle
        ]:
            layout_details.addWidget(label)
        layout.addLayout(layout_details)

        applyStylesheet(self, __file__, 'ControllerStatus.qss')

    def set_status(self, status: Status):
        self.status.setText(status['activeState'].upper())
        self.x_pos.setText(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos.setText(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos.setText(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool_index: int):
        if self.tool_index == tool_index:
            return

        try:
            tool_info = self._get_tool_info(tool_index)
            self.tool.setText(f'Tool: {tool_index} ({tool_info.name})')
        except Exception:
            return

        self.tool_index = tool_index

    def _get_tool_info(self, tool_index: int):
        with SessionLocal() as db_session:
            repository = ToolRepository(db_session)
            return repository.get_tool_by_id(tool_index)

    def set_feedrate(self, feedrate: float):
        self.feedrate.setText(f'Feed rate: {feedrate}')

    def set_spindle(self, spindle: float):
        self.spindle.setText(f'Spindle: {spindle}')
