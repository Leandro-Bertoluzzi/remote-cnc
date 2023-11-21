from components.ControllerStatus import ControllerStatus
from core.database.models.tool import Tool
from PyQt5.QtWidgets import QLabel
import pytest


class TestControllerStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        # Create an instance of ControllerStatus
        self.controller_status = ControllerStatus()
        qtbot.addWidget(self.controller_status)

    def test_controller_status_init(self, helpers):
        # Assertions
        assert helpers.count_widgets(self.controller_status.layout(), QLabel) == 7
        assert self.controller_status.status.text() == 'DISCONNECTED'
        assert self.controller_status.x_pos.text() == 'X: 0.0 (0.0)'
        assert self.controller_status.y_pos.text() == 'Y: 0.0 (0.0)'
        assert self.controller_status.z_pos.text() == 'Z: 0.0 (0.0)'
        assert self.controller_status.tool.text() == 'Tool: xxx'
        assert self.controller_status.feedrate.text() == 'Feed rate: 0'
        assert self.controller_status.spindle.text() == 'Spindle: 0'

    def test_controller_status_set_status(self):
        new_status = {
            'activeState': 'Idle',
            'mpos': {'x': 1.0, 'y': 2.55, 'z': 3.30},
            'wpos': {'x': 6.0, 'y': 7.55, 'z': 8.30},
            'ov': []
        }

        # Call method under test
        self.controller_status.set_status(new_status)

        # Assertions
        assert self.controller_status.status.text() == 'IDLE'
        assert self.controller_status.x_pos.text() == 'X: 1.0 (6.0)'
        assert self.controller_status.y_pos.text() == 'Y: 2.55 (7.55)'
        assert self.controller_status.z_pos.text() == 'Z: 3.3 (8.3)'

    def test_controller_status_set_tool(self):
        new_tool = Tool('New tool', 'It is a really useful tool')

        # Call method under test
        self.controller_status.set_tool(2, new_tool)

        # Assertions
        assert self.controller_status.tool.text() == 'Tool: 2 (New tool)'

    def test_controller_status_set_feedrate(self):
        # Call method under test
        self.controller_status.set_feedrate(1000)

        # Assertions
        assert self.controller_status.feedrate.text() == 'Feed rate: 1000'

    def test_controller_status_set_spindle(self):
        # Call method under test
        self.controller_status.set_spindle(1500)

        # Assertions
        assert self.controller_status.spindle.text() == 'Spindle: 1500'
