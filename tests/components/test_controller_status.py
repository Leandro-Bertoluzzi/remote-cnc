from components.ControllerStatus import ControllerStatus
from core.database.models import Tool
from core.database.repositories.toolRepository import ToolRepository
import pytest


class TestControllerStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        # Create an instance of ControllerStatus
        self.controller_status = ControllerStatus()
        qtbot.addWidget(self.controller_status)

    def test_controller_status_init(self, helpers):
        # Assertions
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

    def test_controller_status_set_tool(self, mocker):
        # Mock DB methods
        test_tool = Tool('Test tool', 'It is a really useful tool')
        mock_db_get_tool_by_id = mocker.patch.object(
            ToolRepository,
            'get_tool_by_id',
            return_value=test_tool
        )

        # Call method under test
        self.controller_status.set_tool(2)

        # Assertions
        assert mock_db_get_tool_by_id.call_count == 1
        assert self.controller_status.tool.text() == 'Tool: 2 (Test tool)'
        assert self.controller_status.tool_index == 2

    def test_controller_status_set_tool_no_change(self, mocker):
        # Set widget initial status
        self.controller_status.tool.setText('Tool: 1 (Initial tool)')
        self.controller_status.tool_index = 1

        # Mock DB methods
        mock_db_get_tool_by_id = mocker.patch.object(ToolRepository, 'get_tool_by_id')

        # Call method under test
        self.controller_status.set_tool(1)

        # Assertions
        assert mock_db_get_tool_by_id.call_count == 0
        assert self.controller_status.tool.text() == 'Tool: 1 (Initial tool)'
        assert self.controller_status.tool_index == 1

    def test_controller_status_set_tool_db_error(self, mocker):
        # Set widget initial status
        self.controller_status.tool.setText('Tool: 1 (Initial tool)')
        self.controller_status.tool_index = 1

        # Mock DB methods
        mock_db_get_tool_by_id = mocker.patch.object(
            ToolRepository,
            'get_tool_by_id',
            side_effect=Exception('mocked-error')
        )

        # Call method under test
        self.controller_status.set_tool(2)

        # Assertions
        assert mock_db_get_tool_by_id.call_count == 1
        assert self.controller_status.tool.text() == 'Tool: 1 (Initial tool)'
        assert self.controller_status.tool_index == 1

    def test_controller_status_set_feedrate(self):
        # Call method under test
        self.controller_status.set_feedrate(1000.00)

        # Assertions
        assert self.controller_status.feedrate.text() == 'Feed rate: 1000.0'

    def test_controller_status_set_spindle(self):
        # Call method under test
        self.controller_status.set_spindle(1500.00)

        # Assertions
        assert self.controller_status.spindle.text() == 'Spindle: 1500.0'
