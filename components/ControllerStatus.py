from core.utils.files import getFileNameInFolder
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class ControllerStatus(QWidget):
    def __init__(self, parent=None):
        super(ControllerStatus, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

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

    def set_status(self, status):
        self.status.setText(status['activeState'].upper())
        self.x_pos.setText(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos.setText(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos.setText(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool_number: int, tool_info):
        self.tool.setText(f'Tool: {tool_number} ({tool_info.name})')

    def set_feedrate(self, feedrate: int):
        self.feedrate.setText(f'Feed rate: {feedrate}')

    def set_spindle(self, spindle: int):
        self.spindle.setText(f'Spindle: {spindle}')
