from core.database.base import Session as SessionLocal
from core.database.repositories.toolRepository import ToolRepository
from helpers.utils import applyStylesheet
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class ControllerStatus(QWidget):
    def __init__(self, parent=None):
        super(ControllerStatus, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.tool_index = 0

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

        applyStylesheet(self, __file__, 'ControllerStatus.qss')

    def set_status(self, status):
        self.status.setText(status['activeState'].upper())
        self.x_pos.setText(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos.setText(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos.setText(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool_index: int):
        if self.tool_index == tool_index:
            return

        try:
            db_session = SessionLocal()
            repository = ToolRepository(db_session)
            tool_info = repository.get_tool_by_id(tool_index)
            self.tool.setText(f'Tool: {tool_index} ({tool_info.name})')
        except Exception:
            return

        self.tool_index = tool_index

    def set_feedrate(self, feedrate: float):
        self.feedrate.setText(f'Feed rate: {feedrate}')

    def set_spindle(self, spindle: float):
        self.spindle.setText(f'Spindle: {spindle}')
