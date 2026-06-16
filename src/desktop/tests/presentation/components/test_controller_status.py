import pytest
from core.domain.entities import Tool
from desktop.presentation.components.ControllerStatus import ControllerStatus
from pytestqt.qtbot import QtBot


class TestControllerStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot):
        self.controller_status = ControllerStatus()
        qtbot.addWidget(self.controller_status)

    def test_controller_status_init(self, helpers):
        # Assertions
        assert self.controller_status.status.text() == "DISCONNECTED"
        assert self.controller_status.x_pos.text() == "X: 0.0 (0.0)"
        assert self.controller_status.y_pos.text() == "Y: 0.0 (0.0)"
        assert self.controller_status.z_pos.text() == "Z: 0.0 (0.0)"
        assert self.controller_status.tool.text() == "Tool: ---"
        assert self.controller_status.feedrate.text() == "Feed rate: 0"
        assert self.controller_status.spindle.text() == "Spindle: 0"

    def test_controller_status_set_status(self):
        new_status = {
            "activeState": "Idle",
            "mpos": {"x": 1.0, "y": 2.55, "z": 3.30},
            "wpos": {"x": 6.0, "y": 7.55, "z": 8.30},
            "ov": [],
        }

        # Call method under test
        self.controller_status.set_status(new_status)

        # Assertions
        assert self.controller_status.status.text() == "IDLE"
        assert self.controller_status.x_pos.text() == "X: 1.0 (6.0)"
        assert self.controller_status.y_pos.text() == "Y: 2.55 (7.55)"
        assert self.controller_status.z_pos.text() == "Z: 3.3 (8.3)"

    def test_controller_status_set_tool(self):
        # Create test tool
        test_tool = Tool("Test tool", "It is a really useful tool")
        test_tool.id = 2

        # Call method under test
        self.controller_status.set_tool(test_tool)

        # Assertions
        assert self.controller_status.tool.text() == "Tool: 2 (Test tool)"

    def test_controller_status_set_tool_none(self):
        # Set widget initial status
        self.controller_status.tool.setText("Tool: 1 (Initial tool)")

        # Call method under test with None
        self.controller_status.set_tool(None)

        # Assertions
        assert self.controller_status.tool.text() == "Tool: ---"

    def test_controller_status_set_feedrate(self):
        # Call method under test
        self.controller_status.set_feedrate(1000.00)

        # Assertions
        assert self.controller_status.feedrate.text() == "Feed rate: 1000.0"

    def test_controller_status_set_spindle(self):
        # Call method under test
        self.controller_status.set_spindle(1500.00)

        # Assertions
        assert self.controller_status.spindle.text() == "Spindle: 1500.0"
