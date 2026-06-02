from unittest.mock import MagicMock

import mocks.grbl as grbl_mocks
import pytest
from adapters.cnc.fakes import FakeSerial
from gateway.adapters.cnc.communicator import GrblCommunicator
from gateway.adapters.cnc.controller import GrblController
from gateway.adapters.cnc.monitor import GrblMonitor
from gateway.adapters.cnc.parsers.grblMsgTypes import (
    GRBL_MSG_FEEDBACK,
    GRBL_MSG_HELP,
    GRBL_MSG_OPTIONS,
    GRBL_MSG_PARAMS,
    GRBL_MSG_PARSER_STATE,
    GRBL_MSG_SETTING,
    GRBL_MSG_STATUS,
    GRBL_MSG_VERSION,
)
from gateway.adapters.cnc.status import GrblStatus
from mocks.logger import FakeLogger
from pytest_mock.plugin import MockerFixture
from serial import SerialException


class TestGrblController:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.fake_serial = FakeSerial()
        self.mock_pubsub = MagicMock()
        self.grbl_controller = GrblController(
            serial=self.fake_serial, logger=FakeLogger(), pubsub_client=self.mock_pubsub
        )
        self.grbl_status = self.grbl_controller.grbl_status

    def _inject_mock_communicator(self, mocker: MockerFixture) -> MagicMock:
        """Injects a MagicMock communicator into the controller.

        Used in tests that verify delegation to the communicator without
        actually connecting to a device.
        """
        mock_comm = mocker.MagicMock(spec=GrblCommunicator)
        self.grbl_controller._communicator = mock_comm
        return mock_comm

    def test_connect_fails_serial(self, mocker: MockerFixture):
        # Mock GrblInitializer.open_connection to raise SerialException
        mock_init_cls = mocker.patch("gateway.adapters.cnc.controller.GrblInitializer")
        mock_init_cls.return_value.open_connection.side_effect = SerialException("mocked error")
        mocker.patch("gateway.adapters.cnc.controller.GrblCommunicator")

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
        # Mock GrblInitializer
        mock_init_cls = mocker.patch("gateway.adapters.cnc.controller.GrblInitializer")
        mock_initializer = mock_init_cls.return_value
        mock_initializer.open_connection.return_value = {
            "firmware": "Grbl",
            "version": "1.1",
            "message": None,
            "raw": "Grbl 1.1",
        }

        # Mock GrblCommunicator — I/O thread is not started for real
        mock_comm_cls = mocker.patch("gateway.adapters.cnc.controller.GrblCommunicator")

        # Call method under test
        response = self.grbl_controller.connect("port", 9600)

        # Assertions — controller orchestrates the initialization steps and starts the thread
        assert response == {
            "firmware": "Grbl",
            "version": "1.1",
            "message": None,
            "raw": "Grbl 1.1",
        }
        assert self.grbl_controller.build_info["version"] == "1.1"
        mock_init_cls.assert_called_once()
        mock_initializer.open_connection.assert_called_once_with("port", 9600, 0.10)
        mock_initializer.handle_post_startup.assert_called_once_with(mock_comm_cls.return_value)
        mock_initializer.queue_initial_queries.assert_called_once_with(mock_comm_cls.return_value)
        mock_comm_cls.return_value.start.assert_called_once()

    @pytest.mark.parametrize("connected", [True, False])
    def test_disconnect(self, mocker: MockerFixture, connected):
        # Mock GRBL status methods
        mocker.patch.object(self.grbl_status, "connected", return_value=connected)
        mock_set_active_state = mocker.patch.object(self.grbl_status, "set_active_state")

        # Mock serial methods — FakeSerial tracks stopConnection calls via stop_call_count

        # Call method under test
        self.grbl_controller.disconnect()

        # Assertions
        assert self.fake_serial.stop_call_count == (1 if connected else 0)
        assert self.grbl_status.get_flag("connected") is False
        assert mock_set_active_state.call_count == (1 if connected else 0)

    @pytest.mark.parametrize("paused", [False, True])
    def test_set_paused(self, mocker: MockerFixture, paused):
        # Mock other methods from controller
        mock_pause = mocker.patch.object(self.grbl_controller, "request_pause")
        mock_resume = mocker.patch.object(self.grbl_controller, "request_resume")

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

        self.grbl_controller.query_status_report()

        comm.request_status_query.assert_called_once()

    def test_query_parser_state(self, mocker: MockerFixture):
        # Flag starts clear
        self.grbl_controller._parser_state_query_in_flight = False
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        self.grbl_controller.query_gcode_parser_state()

        # Command is sent and flag is now set
        mock_command_send.assert_called_once_with("$G")
        assert self.grbl_controller._parser_state_query_in_flight is True

    def test_query_parser_state_skips_when_in_flight(self, mocker: MockerFixture):
        # Simulate a previous $G still waiting for its ok
        self.grbl_controller._parser_state_query_in_flight = True
        mock_command_send = mocker.patch.object(GrblController, "send_command")

        self.grbl_controller.query_gcode_parser_state()

        # No new command should be enqueued
        mock_command_send.assert_not_called()
        assert self.grbl_controller._parser_state_query_in_flight is True

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

    def test_on_ok_calls_ok_hook(self):
        mock_hook = MagicMock()
        self.grbl_controller.register_ok_hook(mock_hook)

        self.grbl_controller._on_ok("G0 X10")

        mock_hook.assert_called_once_with("G0 X10")

    def test_on_ok_no_hook_registered(self):
        """_on_ok must not raise when no ok hook is registered."""
        self.grbl_controller._on_ok("G0 X10")  # should not raise

    def test_on_ok_clears_parser_state_flag(self):
        # Flag is set because a $G was sent
        self.grbl_controller._parser_state_query_in_flight = True

        self.grbl_controller._on_ok("$G")

        assert self.grbl_controller._parser_state_query_in_flight is False

    def test_on_ok_does_not_clear_flag_for_other_commands(self):
        # Flag is set; a non-$G ok must not touch it
        self.grbl_controller._parser_state_query_in_flight = True

        self.grbl_controller._on_ok("G1 X10")

        assert self.grbl_controller._parser_state_query_in_flight is True

    def test_on_error_pauses_and_sets_error(self, mocker: MockerFixture):
        mock_set_error = mocker.patch.object(GrblStatus, "set_error")
        mock_pause = mocker.patch.object(self.grbl_controller, "request_pause")
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

    def test_on_error_clears_parser_state_flag_when_error_was_for_parser_state_query(
        self, mocker: MockerFixture
    ):
        """If GRBL returns error:N for a $G query, ``_parser_state_query_in_flight``
        must be reset so that future calls to ``query_gcode_parser_state()`` are
        not permanently blocked."""
        mocker.patch.object(GrblStatus, "set_error")
        mocker.patch.object(self.grbl_controller, "request_pause")
        payload = {
            "code": 2,
            "message": "G-code word value error",
            "description": "G-code word has invalid value.",
        }
        self.grbl_controller._parser_state_query_in_flight = True

        self.grbl_controller._on_error("$G", payload)

        assert self.grbl_controller._parser_state_query_in_flight is False

    def test_on_error_does_not_clear_parser_state_flag_for_other_commands(
        self, mocker: MockerFixture
    ):
        """An error for any command other than $G must not touch
        ``_parser_state_query_in_flight``."""
        mocker.patch.object(GrblStatus, "set_error")
        mocker.patch.object(self.grbl_controller, "request_pause")
        payload = {
            "code": 2,
            "message": "G-code word value error",
            "description": "G-code word has invalid value.",
        }
        self.grbl_controller._parser_state_query_in_flight = True

        self.grbl_controller._on_error("G1 X10", payload)

        assert self.grbl_controller._parser_state_query_in_flight is True
