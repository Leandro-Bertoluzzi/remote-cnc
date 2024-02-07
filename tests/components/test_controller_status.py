from components.ControllerStatus import ControllerStatus
from core.database.models import Tool
from core.grbl.grblController import GrblController
import logging
from PyQt5.QtWidgets import QLabel
import pytest
import threading


class TestControllerStatus:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        grbl_logger = logging.getLogger('test_logger')
        self.grbl_controller = GrblController(grbl_logger)

        # Create an instance of ControllerStatus
        self.controller_status = ControllerStatus(self.grbl_controller)
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

    def test_controller_status_start_monitor(self, mocker):
        # Mock thread
        mock_thread_create = mocker.patch.object(threading.Thread, '__init__', return_value=None)
        mock_thread_start = mocker.patch.object(threading.Thread, 'start')

        # Call method under test
        self.controller_status.start_monitor()

        # Assertions
        assert mock_thread_create.call_count == 1
        assert mock_thread_start.call_count == 1

    def test_controller_status_stop_monitor(self, mocker):
        # Call method under test
        self.controller_status.stop_monitor()

        # Assertions
        assert self.controller_status.monitor_thread is None

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
