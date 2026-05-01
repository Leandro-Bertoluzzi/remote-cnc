import logging
import re
from typing import Optional

from serial import SerialException

from core.utilities.grbl.constants import GrblCommand, GrblRealtimeCommand
from core.utilities.grbl.grblCommunicator import GrblCommunicator
from core.utilities.grbl.grblInitializer import GrblInitializer
from core.utilities.grbl.grblMonitor import GrblMonitor
from core.utilities.grbl.grblStatus import GrblStatus, GrblStatusFlag
from core.utilities.grbl.grblUtils import build_jog_command, get_grbl_setting
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
from core.utilities.grbl.types import (
    GrblBuildInfo,
    GrblControllerParameters,
    GrblSetting,
    GrblSettings,
)
from core.utilities.serial import SerialService

# Constants
DISCONNECTED = "DISCONNECTED"
SERIAL_TIMEOUT = 0.10  # seconds
RX_BUFFER_SIZE = 128
GRBL_HELP_MESSAGE = "$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x"


class GrblController:
    parameters: GrblControllerParameters = {
        "G54": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G55": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G56": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G57": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G58": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G59": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G28": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G30": {"x": 0.0, "y": 0.0, "z": 0.0},
        "G92": {"x": 0.0, "y": 0.0, "z": 0.0},
        "TLO": 0.000,
        "PRB": {"x": 0.0, "y": 0.0, "z": 0.0, "result": True},
    }

    build_info: GrblBuildInfo = {
        "version": "",
        "comment": "",
        "optionCode": "",
        "blockBufferSize": 15,
        "rxBufferSize": RX_BUFFER_SIZE,
    }

    settings: GrblSettings = {}

    help_text = GRBL_HELP_MESSAGE

    def __init__(self, logger: logging.Logger, *, skip_startup_validation: bool = False):
        # Configure serial interface
        self.serial = SerialService()

        # Configure logger
        self.grbl_monitor = GrblMonitor(logger)

        # Configure status manager
        self.grbl_status = GrblStatus()

        # Configuration
        self._skip_startup_validation = skip_startup_validation

        # Communicator (created on connect)
        self._communicator: Optional[GrblCommunicator] = None

        # State variables
        self.commands_count = 0  # Amount of already processed commands

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_io_alive(self) -> bool:
        """Returns ``True`` if the serial I/O thread is currently running."""
        return self._communicator is not None and self._communicator.alive

    def connect(self, port: str, baudrate: int) -> dict[str, str] | None:
        """Starts the GRBL device connected to the given port."""
        try:
            self.serial.startConnection(port, baudrate, SERIAL_TIMEOUT)
        except SerialException as error:
            self.grbl_monitor.critical(
                f"Failed opening serial port {port} with a baudrate of {baudrate}", exc_info=True
            )
            raise Exception(
                f"Failed opening serial port {port}, "
                "verify and close any other connection you may have"
            ) from error
        self.grbl_monitor.info(
            f"Started USB connection at port {port} with a baudrate of {baudrate}"
        )

        # Build communicator (created fresh on every connect)
        self._communicator = GrblCommunicator(
            serial=self.serial,
            grbl_status=self.grbl_status,
            monitor=self.grbl_monitor,
            on_ok=self._on_ok,
            on_error=self._on_error,
            on_alarm=self._on_alarm,
            on_message=self._on_message,
            on_program_end=lambda: None,
            on_disconnect=self.disconnect,
        )

        # Run the initialization protocol (synchronous pre-thread phase)
        initializer = GrblInitializer(
            serial=self.serial,
            monitor=self.grbl_monitor,
            skip_startup_validation=self._skip_startup_validation,
            on_homing_required=self.handle_homing_cycle,
        )
        startup_payload = initializer.read_startup()

        # Store version from startup message when available
        if "version" in startup_payload:
            self.build_info["version"] = startup_payload["version"]

        # Step 2: optional post-startup alarm check (reads one more line)
        initializer.handle_post_startup(self._communicator)

        # State variables
        self.grbl_status.set_flag(GrblStatusFlag.CONNECTED.value, True)
        self.grbl_status.set_flag(GrblStatusFlag.FINISHED.value, False)
        self.commands_count = 0

        # Start I/O thread
        self._communicator.start()

        # Step 3: queue initial information queries ($I, $G, $$)
        initializer.queue_initial_queries(self._communicator)

        return startup_payload

    def disconnect(self):
        """Ends the communication with the GRBL device."""
        if not self.grbl_status.connected():
            return

        # Stop the I/O thread and close serial
        if self._communicator is not None:
            self._communicator.stop()
        self.serial.stopConnection()
        self.grbl_monitor.info("**Disconnected from device**")

        # State variables
        self.grbl_status.set_flag(GrblStatusFlag.CONNECTED.value, False)
        self.grbl_status.set_active_state(DISCONNECTED)

    # ------------------------------------------------------------------
    # Callbacks from GrblCommunicator
    # ------------------------------------------------------------------

    def _on_ok(self, done_cmd: str) -> None:
        """Called by the communicator when GRBL sends ``ok``."""
        self.commands_count += 1
        self.grbl_monitor.debug(
            f"[Buffer] ok — drained '{done_cmd}', commands_count={self.commands_count}"
        )

    def _on_error(self, error_line: str, payload: dict) -> None:
        """Called by the communicator on ``error:N``.

        Buffer accounting and queue draining are already done by the communicator.
        """
        self.set_paused(True)
        self.grbl_status.set_error(error_line, payload)
        self.grbl_monitor.error(
            f"Error: {payload['message']}. Description: {payload['description']}"
        )

    def _on_alarm(self, alarm_line: str, payload: dict) -> None:
        """Called by the communicator on ``ALARM:N``.

        Buffer accounting and queue draining are already done by the communicator.
        """
        self.grbl_status.set_flag(GrblStatusFlag.ALARM.value, True)
        self.grbl_status.set_flag(GrblStatusFlag.PAUSED.value, True)
        self.grbl_status.set_error(alarm_line, payload)
        self.grbl_monitor.critical(
            f"Alarm activated: {payload['message']}. Description: {payload['description']}"
        )

    def _on_message(self, msg_type: str | None, payload: dict) -> None:
        """Called by the communicator for all non-ack GRBL messages."""
        if msg_type == GRBL_MSG_PARAMS:
            name = payload["name"]
            self.parameters[name] = payload["value"]
            self.grbl_monitor.debug(
                f"Device parameters were successfully updated to {self.parameters}"
            )
            return

        if msg_type == GRBL_MSG_VERSION:
            self.build_info["version"] = payload["version"]
            self.build_info["comment"] = payload["comment"]
            return

        if msg_type == GRBL_MSG_OPTIONS:
            self.build_info["optionCode"] = payload["optionCode"]
            self.build_info["blockBufferSize"] = int(payload["blockBufferSize"])
            self.build_info["rxBufferSize"] = int(payload["rxBufferSize"])
            return

        if msg_type == GRBL_MSG_HELP:
            self.help_text = payload["message"]
            return

        if msg_type == GRBL_MSG_PARSER_STATE:
            # The [GC:...] message is the data payload for a $G query.
            # GRBL still sends a trailing 'ok' for $G (handled by the communicator).
            self.grbl_status.update_parser_state(payload)
            self.grbl_monitor.debug(
                f"Parser state was successfully updated to {self.grbl_status.get_parser_state()}"
            )
            return

        if msg_type == GRBL_MSG_STATUS:
            self.grbl_status.update_status(payload)
            self.grbl_monitor.debug(
                f"Device status was successfully updated to {self.grbl_status.get_status_report()}"
            )
            return

        if msg_type == GRBL_MSG_SETTING:
            key = payload["name"]
            setting = get_grbl_setting(key)
            if setting:
                value: GrblSetting = {
                    "value": payload["value"],
                    "message": setting["message"],
                    "units": setting["units"],
                    "description": setting["description"],
                }
                self.settings[key] = value
            return

        # Response to alarm disable
        if msg_type == GRBL_MSG_FEEDBACK and "Caution: Unlocked" in payload["message"]:
            self.grbl_status.set_flag(GrblStatusFlag.ALARM.value, False)
            self.grbl_status.clear_error()
            self.grbl_monitor.info("Alarm was successfully disabled")
            return

        # Response to checkmode toggled
        if msg_type == GRBL_MSG_FEEDBACK:
            is_check_msg = "Enabled" in payload["message"] or "Disabled" in payload["message"]
            if is_check_msg:
                checkmode = "Enabled" in payload["message"]
                self.grbl_monitor.info(f"Checkmode was successfully updated to {checkmode}")
                return

        self.grbl_monitor.info(f"Unprocessed message from GRBL: {msg_type} — {payload}")

    # INTERNAL STATE MANAGEMENT

    def restart_commands_count(self):
        """Restart the count of already processed commands."""
        self.commands_count = 0

    def get_commands_count(self):
        """Get the count of already processed commands."""
        return self.commands_count

    # ACTIONS

    def set_paused(self, paused: bool):
        self.grbl_status.set_flag(GrblStatusFlag.PAUSED.value, paused)

        if paused:
            self.grbl_pause()
            return

        self.grbl_resume()

    def send_command(self, command: str):
        """Adds a GCODE line or a GRBL command to the serial queue."""
        tosend = command.strip()

        if not tosend:
            self.commands_count += 1
            return

        comment_pattern = re.compile(r"(^\(.*\)$)|(^;.*)")
        if comment_pattern.match(tosend):
            self.commands_count += 1
            return

        if self._communicator is not None:
            self._communicator.send(tosend)

    def handle_homing_cycle(self):
        """Runs the GRBL device's homing cycle."""
        # self.send_command(GrblCommand.HOMING.value)

        # Technical debt: Temporary solution, disable alarm
        self.disable_alarm()

    def disable_alarm(self):
        """Disables an alarm."""
        self.send_command(GrblCommand.DISABLE_ALARM.value)

    def toggle_check_mode(self):
        """Enables/Disables the "check G-code" mode.

        With this mode enabled, the user can stream a G-code program to Grbl,
        where it will parse it, error-check it, and report ok's and errors
        without powering on anything or moving.
        """
        self.send_command(GrblCommand.CHECK_MODE.value)

    def jog(
        self,
        x: float,
        y: float,
        z: float,
        feedrate: float,
        *,
        units=None,
        distance_mode=None,
        machine_coordinates=False,
    ):
        """Executes a 'jog' action.

        JOG mode is also called jogging mode.
        In this mode, the CNC machine is used to operate manually.
        """
        jog_command = build_jog_command(
            x,
            y,
            z,
            feedrate,
            units=units,
            distance_mode=distance_mode,
            machine_coordinates=machine_coordinates,
        )
        self.send_command(jog_command)

    def set_settings(self, settings: dict[str, str]):
        """Updates the value of the given GRBL settings."""
        for key, value in settings.items():
            self.send_command(f"{key}={value}")

    # REAL TIME COMMANDS

    def _send_realtime(self, cmd: bytes, label: str):
        if self._communicator is not None:
            self._communicator.send_realtime(cmd, label)

    def grbl_pause(self):
        """
        Feed Hold: Places Grbl into a suspend or HOLD state.
        If in motion, the machine will decelerate to a stop and then be suspended.
        """
        self._send_realtime(GrblRealtimeCommand.FEED_HOLD.value, "PAUSE")

    def grbl_resume(self):
        """
        Cycle Start / Resume: Resumes a feed hold, a safety door/parking state
        when the door is closed, and the M0 program pause states.
        """
        self._send_realtime(GrblRealtimeCommand.CYCLE_START.value, "RESUME")

    def grbl_soft_reset(self):
        """
        Soft-Reset: Halts and safely resets Grbl without a power-cycle.
        - If reset while in motion, Grbl will throw an alarm to indicate position may be
        lost from the motion halt.
        - If reset while not in motion, position is retained and re-homing is not required.
        """
        self._send_realtime(GrblRealtimeCommand.SOFT_RESET.value, "STOP")

        # Tell the serial_io thread to stop streaming
        self.grbl_status.set_flag(GrblStatusFlag.STOP.value, True)

    def queryStatusReport(self):
        """Queries the GRBL device's current status.

        Instead of writing directly from the calling thread, this method sets a
        flag that is consumed by the I/O thread on its next iteration.
        This ensures the ``?`` byte is never interleaved with other I/O performed
        by the serial thread, which would corrupt the GRBL response stream.
        """
        if self._communicator is not None:
            self._communicator.request_status_query()

    # QUERIES

    def query_gcode_parser_state(self):
        """Queries the GRBL device's current parser state."""
        self.send_command(GrblCommand.PARSER_STATE.value)

    def query_grbl_help(self):
        """
        Queries the GRBL 'help' message.
        This message contains all valid GRBL commands.
        """
        self.send_command(GrblCommand.HELP.value)

    def query_grbl_params(self):
        """Queries the GRBL device's current parameter data."""
        self.send_command(GrblCommand.PARAMETERS.value)

    def query_grbl_settings(self):
        """Queries the list of GRBL settings with their current values."""
        self.send_command(GrblCommand.SETTINGS.value)

    def query_build_info(self):
        """Queries some GRBL device's (firmware) build information."""
        self.send_command(GrblCommand.BUILD.value)

    # GETTERS

    def get_parameters(self):
        """Returns the GRBL device's current parameter data."""
        return self.parameters

    def get_grbl_settings(self):
        """Returns a dictionary with the firmware settings."""
        return self.settings

    def get_build_info(self):
        """Returns the firmware's build information."""
        return self.build_info

    def get_buffer_fill(self) -> float:
        """
        Returns how filled the GRBL command buffer is as a percentage,
        useful to monitor buffer usage.
        """
        if self._communicator is not None:
            return self._communicator.get_buffer_fill()
        return 0.0
