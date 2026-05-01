import logging
from unittest.mock import MagicMock

import mocks.grbl as grbl_mocks
import pytest
from core.utilities.grbl.grblCommunicator import GrblCommunicator
from core.utilities.grbl.grblController import GrblController
from core.utilities.grbl.grblMonitor import GrblMonitor
from core.utilities.grbl.grblStatus import GrblStatus
from core.utilities.grbl.parsers.grblMsgTypes import (
    GRBL_MSG_FEEDBACK,
    GRBL_MSG_HELP,
    GRBL_MSG_OPTIONS,
    GRBL_MSG_PARAMS,
    GRBL_MSG_PARSER_STATE,
    GRBL_MSG_SETTING,
    GRBL_MSG_STATUS,
    GRBL_MSG_VERSION,
)
from core.utilities.serial import SerialService
from pytest_mock.plugin import MockerFixture
from serial import SerialException


# Test fixture for setting up and tearing down the SerialService instance
@pytest.fixture
def serial_service():
    service = SerialService()
    yield service
    service.stopConnection()


class TestGrblController:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        grbl_logger = logging.getLogger("test_logger")
        self.grbl_controller = GrblController(grbl_logger)
        self.grbl_status = self.grbl_controller.grbl_status

        # Mock logger methods
        mocker.patch.object(GrblMonitor, "debug")
        mocker.patch.object(GrblMonitor, "info")
        mocker.patch.object(GrblMonitor, "warning")
        mocker.patch.object(GrblMonitor, "error")
        mocker.patch.object(GrblMonitor, "critical")
        mocker.patch.object(GrblMonitor, "sent")
        mocker.patch.object(GrblMonitor, "received")

    def _inject_mock_communicator(self, mocker: MockerFixture) -> MagicMock:
        """Injects a MagicMock communicator into the controller.

        Used in tests that verify delegation to the communicator without
        actually connecting to a device.
        """
        mock_comm = mocker.MagicMock(spec=GrblCommunicator)
        self.grbl_controller._communicator = mock_comm
        return mock_comm

    def test_connect_fails_serial(self, mocker: MockerFixture):
        # Mock serial methods
        mocker.patch.object(
            SerialService, "startConnection", side_effect=SerialException("mocked error")
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.connect("test-port", 9600)

        # Assertions
        expected_error_msg = (
            "Failed opening serial port test-port, "
            "verify and close any other connection you may have"
        )
        assert str(error.value) == expected_error_msg

    def test_connect(self, mocker: MockerFixture):
        # Mock serial connection
        mock_serial_connect = mocker.patch.object(SerialService, "startConnection")

        # Mock GrblInitializer
        mock_init_cls = mocker.patch("core.utilities.grbl.grblController.GrblInitializer")
        mock_initializer = mock_init_cls.return_value
        mock_initializer.read_startup.return_value = {
            "firmware": "Grbl",
            "version": "1.1",
            "message": None,
            "raw": "Grbl 1.1",
        }

        # Mock GrblCommunicator — I/O thread is not started for real
        mock_comm_cls = mocker.patch("core.utilities.grbl.grblController.GrblCommunicator")

        # Call method under test
        response = self.grbl_controller.connect("port", 9600)

        # Assertions — controller orchestrates the 3 steps and starts the thread
        assert response == {
            "firmware": "Grbl",
            "version": "1.1",
            "message": None,
            "raw": "Grbl 1.1",
        }
        assert self.grbl_controller.build_info["version"] == "1.1"
        mock_serial_connect.assert_called_once()
        mock_init_cls.assert_called_once()
        mock_initializer.read_startup.assert_called_once()
        mock_initializer.handle_post_startup.assert_called_once_with(mock_comm_cls.return_value)
        mock_initializer.queue_initial_queries.assert_called_once_with(mock_comm_cls.return_value)
        mock_comm_cls.return_value.start.assert_called_once()

    @pytest.mark.parametrize("connected", [True, False])
    def test_disconnect(self, mocker: MockerFixture, connected):
        # Mock GRBL status methods
        mocker.patch.object(self.grbl_status, "connected", return_value=connected)
        mock_set_active_state = mocker.patch.object(self.grbl_status, "set_active_state")

        # Mock serial methods
        mock_serial_disconnect = mocker.patch.object(SerialService, "stopConnection")

        # Call method under test
        self.grbl_controller.disconnect()

        # Assertions
        assert mock_serial_disconnect.call_count == (1 if connected else 0)
        assert self.grbl_status.get_flag("connected") is False
        assert mock_set_active_state.call_count == (1 if connected else 0)

    @pytest.mark.parametrize("paused", [False, True])
    def test_set_paused(self, mocker: MockerFixture, paused):
        # Mock other methods from controller
        mock_pause = mocker.patch.object(self.grbl_controller, "grbl_pause")
        mock_resume = mocker.patch.object(self.grbl_controller, "grbl_resume")

        # Call method under test
        self.grbl_controller.set_paused(paused)

        # Assertions
        assert self.grbl_status.paused() == paused
        assert mock_pause.call_count == (1 if paused else 0)
        assert mock_resume.call_count == (0 if paused else 1)

    def test_send_command(self, mocker: MockerFixture):
        comm = self._inject_mock_communicator(mocker)

        self.grbl_controller.send_command("$")

        comm.send.assert_called_once_with("$")

    def test_handle_homing_cycle(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_disable_alarm = mocker.patch.object(GrblController, "disable_alarm")

        # Call the method under test
        self.grbl_controller.handle_homing_cycle()

        # Assertions
        assert mock_disable_alarm.call_count == 1

    def test_disable_alarm(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.disable_alarm()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$X")

    def test_query_status_report(self, mocker: MockerFixture):
        comm = self._inject_mock_communicator(mocker)

        self.grbl_controller.queryStatusReport()

        comm.request_status_query.assert_called_once()

    def test_query_parser_state(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.query_gcode_parser_state()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$G")

    def test_query_help(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.query_grbl_help()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$")

    def test_toggle_checkmode(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.toggle_check_mode()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$C")

    def test_jog(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.jog(1.00, 2.00, 3.00, 500.00)

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$J=X1.0 Y2.0 Z3.0 F500.0")

    def test_set_settings(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.set_settings({"$22": "1", "$23": "5", "$27": "5.200"})

        # Assertions
        assert mock_command_send.call_count == 3

    def test_query_build_info(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.query_build_info()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$I")

    def test_query_settings(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.query_grbl_settings()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$$")

    def test_query_grbl_parameters(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        # Call the method under test
        self.grbl_controller.query_grbl_params()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with("$#")

    def test_getters(self):
        # Set test values for controller's parameters
        self.grbl_controller.parameters = grbl_mocks.grbl_parameters
        self.grbl_controller.settings = grbl_mocks.grbl_settings
        self.grbl_controller.build_info = grbl_mocks.grbl_build_info

        # Call methods under test
        parameters = self.grbl_controller.get_parameters()
        settings = self.grbl_controller.get_grbl_settings()
        build_info = self.grbl_controller.get_build_info()

        # Assertions
        assert parameters == grbl_mocks.grbl_parameters
        assert settings == grbl_mocks.grbl_settings
        assert build_info == grbl_mocks.grbl_build_info

    @pytest.mark.parametrize(
        "occupied,expected", [(0, 0.0), (16, 12.5), (32, 25.0), (64, 50.0), (128, 100.0)]
    )
    def test_get_buffer_fill(self, mocker: MockerFixture, occupied, expected):
        comm = self._inject_mock_communicator(mocker)
        comm.get_buffer_fill.return_value = expected

        value = self.grbl_controller.get_buffer_fill()

        assert value == expected
        comm.get_buffer_fill.assert_called_once()

    # PARSER / MESSAGE CALLBACKS
    # Tests call _on_message(msg_type, payload) directly, bypassing GrblLineParser.
    # Payload format matches what _handle_response forwards (no 'raw' key).

    def test_on_message_grbl_parameters(self):
        self.grbl_controller.parameters = {}

        params = [
            ("G54", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G55", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G56", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G57", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G58", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G59", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G28", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G30", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("G92", {"x": 0.0, "y": 0.0, "z": 0.0}),
            ("TLO", 0.0),
            ("PRB", {"x": 0.0, "y": 0.0, "z": 0.0, "result": False}),
        ]
        for name, value in params:
            self.grbl_controller._on_message(GRBL_MSG_PARAMS, {"name": name, "value": value})

        assert self.grbl_controller.parameters == {
            "G54": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G55": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G56": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G57": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G58": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G59": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G28": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G30": {"x": 0.0, "y": 0.0, "z": 0.0},
            "G92": {"x": 0.0, "y": 0.0, "z": 0.0},
            "TLO": 0.0,
            "PRB": {"x": 0.0, "y": 0.0, "z": 0.0, "result": False},
        }

    def test_on_message_grbl_settings(self):
        self.grbl_controller.settings = {}

        self.grbl_controller._on_message(GRBL_MSG_SETTING, {"name": "$0", "value": "100.200"})
        self.grbl_controller._on_message(GRBL_MSG_SETTING, {"name": "$102", "value": "1.000"})

        assert self.grbl_controller.settings == {
            "$0": {
                "value": "100.200",
                "message": "Step pulse time",
                "units": "microseconds",
                "description": "Sets time length per step. Minimum 3usec.",
            },
            "$102": {
                "value": "1.000",
                "message": "Z-axis travel resolution",
                "units": "step/mm",
                "description": "Z-axis travel resolution in steps per millimeter.",
            },
        }

    @pytest.mark.parametrize(
        "payloads,expected",
        [
            (
                [
                    (GRBL_MSG_VERSION, {"version": "1.1d.20161014", "comment": ""}),
                    (
                        GRBL_MSG_OPTIONS,
                        {"optionCode": "VL", "blockBufferSize": "15", "rxBufferSize": "128"},
                    ),
                ],
                {
                    "version": "1.1d.20161014",
                    "comment": "",
                    "optionCode": "VL",
                    "blockBufferSize": 15,
                    "rxBufferSize": 128,
                },
            ),
            (
                [
                    (
                        GRBL_MSG_OPTIONS,
                        {"optionCode": "VL", "blockBufferSize": "15", "rxBufferSize": "128"},
                    )
                ],
                {"optionCode": "VL", "blockBufferSize": 15, "rxBufferSize": 128},
            ),
            (
                [(GRBL_MSG_VERSION, {"version": "1.1d.20161014", "comment": ""})],
                {"version": "1.1d.20161014", "comment": ""},
            ),
        ],
    )
    def test_on_message_grbl_build_info(self, payloads, expected):
        self.grbl_controller.build_info = {}

        for msg_type, payload in payloads:
            self.grbl_controller._on_message(msg_type, payload)

        assert self.grbl_controller.build_info == expected

    @pytest.mark.parametrize("message,expected_state", [("Enabled", True), ("Disabled", False)])
    def test_on_message_checkmode_feedback(self, mocker: MockerFixture, message, expected_state):
        mock_monitor_info = mocker.patch.object(GrblMonitor, "info")

        self.grbl_controller._on_message(GRBL_MSG_FEEDBACK, {"message": message})

        mock_monitor_info.assert_called_once_with(
            f"Checkmode was successfully updated to {expected_state}"
        )

    def test_on_message_help(self):
        self.grbl_controller.help_text = ""
        msg = "$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x"

        self.grbl_controller._on_message(GRBL_MSG_HELP, {"message": msg})

        assert self.grbl_controller.help_text == msg

    def test_on_message_parser_state(self):
        payload = {
            "modal": {
                "motion": "G38.2",
                "wcs": "G54",
                "plane": "G17",
                "units": "G21",
                "distance": "G91",
                "feedrate": "G94",
                "program": "M0",
                "spindle": "M5",
                "coolant": ["M7", "M8"],
            },
            "tool": 0,
            "feedrate": 20.0,
            "spindle": 0.0,
        }

        self.grbl_controller._on_message(GRBL_MSG_PARSER_STATE, payload)

        assert self.grbl_status.get_parser_state() == payload

    def test_on_message_status_report(self):
        payload = {
            "activeState": "Idle",
            "mpos": {"x": 5.0, "y": 2.0, "z": 0.0},
            "wpos": None,
            "feedrate": 0.0,
            "spindle": 0,
            "ov": [100, 100, 100],
            "subState": None,
            "wco": None,
            "pinstate": None,
            "buffer": None,
            "line": None,
            "accessoryState": None,
        }

        self.grbl_controller._on_message(GRBL_MSG_STATUS, payload)

        assert self.grbl_status.get_status_report()["activeState"] == "Idle"
        assert self.grbl_status.get_status_report()["mpos"] == {"x": 5.0, "y": 2.0, "z": 0.0}

    def test_on_message_disable_alarm_feedback(self):
        self.grbl_controller._on_message(GRBL_MSG_FEEDBACK, {"message": "Caution: Unlocked"})

        assert self.grbl_status.is_alarm() is False

    # ACK callbacks (_on_ok, _on_error, _on_alarm)

    def test_on_ok_increments_commands_count(self):
        initial = self.grbl_controller.commands_count
        self.grbl_controller._on_ok("G0 X10")
        assert self.grbl_controller.commands_count == initial + 1

    def test_on_error_pauses_and_sets_error(self, mocker: MockerFixture):
        mock_set_error = mocker.patch.object(GrblStatus, "set_error")
        mock_pause = mocker.patch.object(self.grbl_controller, "grbl_pause")
        payload = {
            "code": 25,
            "message": "Invalid gcode ID:25",
            "description": "Repeated g-code word found in block.",
        }

        self.grbl_controller._on_error("G54 G54", payload)

        assert self.grbl_status.paused() is True
        mock_set_error.assert_called_once_with("G54 G54", payload)
        mock_pause.assert_called_once()

    def test_on_alarm_sets_error_and_logs(self, mocker: MockerFixture):
        mock_set_error = mocker.patch.object(GrblStatus, "set_error")
        mock_monitor_critical = mocker.patch.object(GrblMonitor, "critical")
        payload = {
            "code": 6,
            "message": "Homing fail",
            "description": "Homing fail. The active homing cycle was reset.",
        }

        self.grbl_controller._on_alarm("$H", payload)

        assert self.grbl_status.get_flag("alarm") is True
        assert self.grbl_status.get_flag("paused") is True
        mock_set_error.assert_called_once_with("$H", payload)
        mock_monitor_critical.assert_called_once_with(
            "Alarm activated: Homing fail. Description: Homing fail. "
            "The active homing cycle was reset."
        )
