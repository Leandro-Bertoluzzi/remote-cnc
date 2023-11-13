from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class ControllerStatus(QWidget):
    def __init__(self, parent=None):
        super(ControllerStatus, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        self.status = QLabel('DISCONNECTED')
        self.x_pos = QLabel('X: 0.0 (0.0)')
        self.y_pos = QLabel('Y: 0.0 (0.0)')
        self.z_pos = QLabel('Z: 0.0 (0.0)')
        self.tool = QLabel('Tool: 1 (Mecha 5mm)')
        self.feedrate = QLabel('Feed rate: 0')
        self.spindle = QLabel('Spindle: 0')

        layout.addWidget(self.status)
        layout.addWidget(self.x_pos)
        layout.addWidget(self.y_pos)
        layout.addWidget(self.z_pos)
        layout.addWidget(self.tool)
        layout.addWidget(self.feedrate)
        layout.addWidget(self.spindle)

    def set_status(self, status):
        self.status = QLabel(status['activeState'].upper())
        self.x_pos = QLabel(f"X: {status['mpos']['x']} ({status['wpos']['x']})")
        self.y_pos = QLabel(f"Y: {status['mpos']['y']} ({status['wpos']['y']})")
        self.z_pos = QLabel(f"Z: {status['mpos']['z']} ({status['wpos']['z']})")

    def set_tool(self, tool_number: int, tool_info):
        self.tool = QLabel(f'Tool: {tool_number} ({tool_info.name})')

    def set_feedrate(self, feedrate: int):
        self.feedrate = QLabel(f'Feed rate: {feedrate}')

    def set_spindle(self, spindle: int):
        self.spindle = QLabel(f'Spindle: {spindle}')
