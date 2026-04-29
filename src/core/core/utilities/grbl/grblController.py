import logging
import sys
import threading
import time
from queue import Empty, Queue
from typing import Optional

from serial import SerialException

from core.config import GRBL_SIMULATION
from core.utilities.gcode.constants import GCODE_PROGRAM_END_CODES
from core.utilities.grbl.constants import GrblCommand, GrblRealtimeCommand
from core.utilities.grbl.grblLineParser import GrblLineParser
from core.utilities.grbl.grblMonitor import GrblMonitor
from core.utilities.grbl.grblStatus import GrblStatus, GrblStatusFlag
from core.utilities.grbl.grblUtils import build_jog_command, get_grbl_setting
from core.utilities.grbl.parsers.grblMsgTypes import (
    GRBL_MSG_ALARM,
    GRBL_MSG_FEEDBACK,
    GRBL_MSG_HELP,
    GRBL_MSG_OPTIONS,
    GRBL_MSG_PARAMS,
    GRBL_MSG_PARSER_STATE,
    GRBL_MSG_SETTING,
    GRBL_MSG_STARTUP,
    GRBL_MSG_STATUS,
    GRBL_MSG_VERSION,
    GRBL_RESULT_ERROR,
    GRBL_RESULT_OK,
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

# GRBL query commands: these commands request information and are safe to send
# in any controller state (including paused/error).
GRBL_QUERY_COMMANDS = {"$G", "$$", "$#", "$I", "$N"}


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

    def __init__(self, logger: logging.Logger):
        # Configure serial interface
        self.serial = SerialService()
        self.queue: Queue[str] = Queue()  # Command queue to be sent to GRBL
        self.serial_thread: Optional[threading.Thread] = None

        # Configure logger
        self.grbl_monitor = GrblMonitor(logger)

        # Configure status manager
        self.grbl_status = GrblStatus()

        # State variables
        self._sumcline = 0  # Amount of bytes in GRBL buffer
        self.commands_count = 0  # Amount of already processed commands
        self._serial_io_alive = False  # True while the serial_io thread is running
        self._status_query_pending = False  # Set True from main thread; consumed inside serial_io

    def connect(self, port: str, baudrate: int) -> dict[str, str] | None:
        """Starts the GRBL device connected to the given port."""
        try:
            response = self.serial.startConnection(port, baudrate, SERIAL_TIMEOUT)
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

        # Handle response
        msgType, payload = GrblLineParser.parse(response)
        self.grbl_monitor.received(response, msgType, payload)

        if not GRBL_SIMULATION:
            if msgType != GRBL_MSG_STARTUP:
                self.grbl_monitor.critical("Failed starting connection with GRBL")
                raise Exception("Failed starting connection with GRBL: ", payload)
            self.build_info["version"] = payload["version"]

        responsePayload = payload

        # -- Startup alarm message validation --
        # [MSG:'$H'|'$X' to unlock] - Alarm state is active at initialization.
        # This message serves as a reminder note on how to cancel the alarm state.
        # All g-code commands and some ‘$’ are blocked until the alarm state is cancelled
        # via homing $H or unlocking $X.
        # Only appears immediately after the Grbl welcome message when initialized with an alarm.
        try:
            response = self.serial.readLine()
        except SerialException:
            self.grbl_monitor.critical(
                f"Error reading response from GRBL: {str(sys.exc_info()[1])}"
            )
            self.serial.stopConnection()
            return
        msgType, payload = GrblLineParser.parse(response)

        if (msgType == GRBL_MSG_FEEDBACK) and ("$H" in payload["message"]):
            self.grbl_monitor.warning("Homing cycle required at startup, handling...")
            self.handle_homing_cycle()

        # State variables
        self.grbl_status.set_flag(GrblStatusFlag.CONNECTED.value, True)
        self.grbl_status.set_flag(GrblStatusFlag.FINISHED.value, False)
        self.commands_count = 0

        # Start serial communication
        self.serial_thread = threading.Thread(target=self.serial_io)
        self.serial_thread.start()

        return responsePayload

    def disconnect(self):
        """Ends the communication with the GRBL device."""
        if not self.grbl_status.connected():
            return

        # Stops communication with serial port
        self.serial_thread = None
        self.serial.stopConnection()
        self.grbl_monitor.info("**Disconnected from device**")

        # State variables
        self.grbl_status.set_flag(GrblStatusFlag.CONNECTED.value, False)
        self.grbl_status.set_active_state(DISCONNECTED)

    def parse_response(self, response: str, cline: list[int], sline: list[str]):
        """Process the response from GRBL and update controller state."""

        def removeProcessedCommand() -> str:
            if cline:
                del cline[0]
            if sline:
                return sline.pop(0)
            return ""

        try:
            msgType, payload = GrblLineParser.parse(response)
        except Exception as error:
            self.grbl_monitor.error(
                f"Error parsing response from GRBL.\nResponse: {response}\nError: {str(error)}"
            )
            return
        self.grbl_monitor.received(response, msgType, payload)

        # Process parsed response
        if msgType == GRBL_RESULT_OK:
            done_cmd = removeProcessedCommand()
            self._sumcline = sum(cline)
            self.commands_count += 1
            self.grbl_monitor.debug(
                f"[Buffer] ok — drained '{done_cmd}', "
                f"cline_sum={self._sumcline}/{RX_BUFFER_SIZE}, pending={len(cline)}"
            )
            return

        if msgType == GRBL_RESULT_ERROR:
            self.set_paused(True)
            error_line = removeProcessedCommand()
            # GRBL discards all remaining buffered commands on error — they will
            # never receive ok responses.  Clear the phantom entries so that
            # buffer accounting resets to zero and subsequent queries can be sent.
            cline.clear()
            sline.clear()
            self._sumcline = 0
            del payload["raw"]
            self.grbl_status.set_error(error_line, payload)
            self.grbl_monitor.error(
                f"Error: {payload['message']}. Description: {payload['description']}"
            )
            self._empty_queue()
            return

        if msgType == GRBL_MSG_ALARM:
            self.grbl_status.set_flag(GrblStatusFlag.ALARM.value, True)
            self.grbl_status.set_flag(GrblStatusFlag.PAUSED.value, True)
            error_line = removeProcessedCommand()
            # Same as error: GRBL abandons buffered commands on alarm.
            cline.clear()
            sline.clear()
            self._sumcline = 0
            del payload["raw"]
            self.grbl_status.set_error(error_line, payload)
            self.grbl_monitor.critical(
                f"Alarm activated: {payload['message']}. Description: {payload['description']}"
            )
            self._empty_queue()
            return

        if msgType == GRBL_MSG_PARAMS:
            name = payload["name"]
            self.parameters[name] = payload["value"]
            self.grbl_monitor.debug(
                f"Device parameters were successfully updated to {self.parameters}"
            )
            return

        if msgType == GRBL_MSG_VERSION:
            self.build_info["version"] = payload["version"]
            self.build_info["comment"] = payload["comment"]
            return

        if msgType == GRBL_MSG_OPTIONS:
            self.build_info["optionCode"] = payload["optionCode"]
            self.build_info["blockBufferSize"] = int(payload["blockBufferSize"])
            self.build_info["rxBufferSize"] = int(payload["rxBufferSize"])
            return

        if msgType == GRBL_MSG_HELP:
            self.help_text = payload["message"]
            return

        if msgType == GRBL_MSG_PARSER_STATE:
            # The [GC:...] message is the data payload for a $G query.
            # GRBL still sends a trailing 'ok' for $G, which is the real
            # acknowledgment that the RX buffer slot has been freed.  Do NOT
            # call removeProcessedCommand() here — the subsequent 'ok' handler
            # is responsible for draining sline/cline.  Calling it here too
            # would remove an extra entry for every $G sent, causing buffer
            # accounting drift and eventual RX buffer overflow (error:1).
            del payload["raw"]
            self.grbl_status.update_parser_state(payload)
            self.grbl_monitor.debug(
                f"Parser state was successfully updated to {self.grbl_status.get_parser_state()}"
            )
            return

        if msgType == GRBL_MSG_STATUS:
            del payload["raw"]
            self.grbl_status.update_status(payload)
            self.grbl_monitor.debug(
                f"Device status was successfully updated to {self.grbl_status.get_status_report()}"
            )
            return

        if msgType == GRBL_MSG_SETTING:
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

        # Response to alarm disable
        if (msgType == GRBL_MSG_FEEDBACK) and ("Caution: Unlocked" in payload["message"]):
            self.grbl_status.set_flag(GrblStatusFlag.ALARM.value, False)
            self.grbl_status.clear_error()
            self.grbl_monitor.info("Alarm was successfully disabled")
            return

        # Response to checkmode toggled
        if msgType == GRBL_MSG_FEEDBACK:
            is_check_msg = "Enabled" in payload["message"] or "Disabled" in payload["message"]
            if is_check_msg:
                checkmode = "Enabled" in payload["message"]
                self.grbl_monitor.info(f"Checkmode was successfully updated to {checkmode}")
                return

        self.grbl_monitor.info(f"Unprocessed message from GRBL: {response}")

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

        import re

        comment_pattern = re.compile(r"(^\(.*\)$)|(^;.*)")
        if comment_pattern.match(tosend):
            self.commands_count += 1
            return

        self.queue.put(tosend)

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
        try:
            self.serial.sendBytes(cmd)
        except SerialException as e:
            self.grbl_monitor.error(f"Error sending {label}: {e}")
            return

        cmd_str = repr(cmd)[2:-1]  # Convert bytes to string for logging
        self.grbl_monitor.sent(cmd_str)
        self.grbl_monitor.info(f"Requested {label}")

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
        flag that is consumed by the ``serial_io`` thread on its next iteration.
        This ensures the ``?`` byte is never interleaved with other I/O performed
        by the serial thread, which would corrupt the GRBL response stream.
        """
        self._status_query_pending = True

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
        return self._sumcline * 100.0 / RX_BUFFER_SIZE

    # COMMUNICATION

    def _empty_queue(self):
        """Empties the command queue."""
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except Empty:
                break

    def serial_io(self):
        """Thread performing I/O on serial line.

        Responsible only for:
        - Dequeueing commands from the internal queue
        - Tracking the GRBL RX buffer via ``cline``
        - Sending commands over serial when buffer space is available
        - Reading and parsing GRBL responses
        - Handling stop requests and program-end codes
        """
        cline: list[int] = []  # length of pipeline commands
        sline: list[str] = []  # pipeline commands
        tosend = None  # next string to send
        exit_reason = "loop ended (serial_thread set to None)"

        self._serial_io_alive = True
        self.grbl_monitor.info("serial_io thread started")

        while self.serial_thread:
            try:
                # Send pending status query (set by queryStatusReport() from main thread).
                # Doing this here ensures the '?' byte is never written concurrently with
                # a readLine() or sendLine() call in this same thread.
                if self._status_query_pending:
                    try:
                        self.serial.sendBytes(GrblRealtimeCommand.STATUS_REPORT.value)
                        self.grbl_monitor.sent("?", debug=True)
                    except SerialException as e:
                        self.grbl_monitor.error(f"Error sending STATUS: {e}")
                    finally:
                        self._status_query_pending = False
                    # Give the device a full iteration to respond before sending
                    # the next queued command.  Sending '?' and a G-code line in
                    # the same OS write burst causes grbl-sim's real-time handler
                    # to consume bytes from the command that follows, corrupting
                    # the stream and permanently stalling the 'ok' flow.
                    continue

                # Fetch new command to send if the queue has work and either:
                # (a) the controller is not paused, or
                # (b) the next command is a query (safe in any state).
                # We peek at queue.queue[0] before extracting so we can read the
                # command without consuming it. This is safe because serial_io is
                # the sole consumer of the queue.
                if tosend is None and self.queue.qsize() > 0:
                    next_cmd = self.queue.queue[0]  # peek
                    if not self.grbl_status.paused() or next_cmd in GRBL_QUERY_COMMANDS:
                        try:
                            tosend = self.queue.get_nowait()
                        except Empty:
                            continue

                    if tosend is not None:
                        # If necessary, all modifications in tosend should be
                        # done before adding it to cline

                        # Bookkeeping of the buffers
                        # +1 accounts for the '\n' appended by sendLine()
                        sline.append(tosend)
                        cline.append(len(tosend) + 1)

                # Anything to receive?
                if self.serial.waiting() or tosend is None:
                    try:
                        response = self.serial.readLine()
                    except SerialException:
                        self.grbl_monitor.error(
                            f"Error reading response from GRBL: {str(sys.exc_info()[1])}"
                        )
                        self._empty_queue()
                        self.disconnect()
                        exit_reason = "SerialException on read"
                        break

                    if not response:
                        pass
                    else:
                        self.parse_response(response, cline, sline)

                # Received external message to stop
                if self.grbl_status.get_flag(GrblStatusFlag.STOP.value):
                    self._empty_queue()
                    tosend = None
                    self.grbl_status.set_flag(GrblStatusFlag.STOP.value, False)
                    self.grbl_monitor.info("STOP request processed")

                # Send command to GRBL
                if tosend is not None and sum(cline) < RX_BUFFER_SIZE:
                    self._sumcline = sum(cline)

                    try:
                        self.serial.sendLine(tosend)
                    except SerialException:
                        self.grbl_monitor.error(
                            f"Error sending command to GRBL: {str(sys.exc_info()[1])}"
                        )
                        error_data = {
                            "code": 0,
                            "message": "Communication error",
                            "description": str(sys.exc_info()[1]),
                        }
                        self.grbl_status.set_error(tosend, error_data)
                        self._empty_queue()
                        self.disconnect()
                        exit_reason = "SerialException on write"
                        break

                    self.grbl_monitor.sent(tosend)
                    self.grbl_monitor.debug(
                        f"[Buffer] Sent '{tosend}', "
                        f"cline_sum={self._sumcline}/{RX_BUFFER_SIZE}, pending={len(cline)}"
                    )

                    # Check if end of program
                    if tosend.strip() in GCODE_PROGRAM_END_CODES:
                        self.grbl_monitor.info(f"A program end command was found: {tosend}")
                        self.grbl_status.set_flag(GrblStatusFlag.FINISHED.value, True)
                        self._empty_queue()
                        exit_reason = "program end command"
                        break

                    tosend = None
                elif tosend is not None:
                    self.grbl_monitor.debug(
                        f"[Buffer] Full — waiting to send '{tosend}', "
                        f"cline_sum={sum(cline)}/{RX_BUFFER_SIZE}, pending={len(cline)}"
                    )

            except Exception:
                # An unexpected bug in one iteration must not kill the I/O thread.
                # Log it as critical and let the loop continue so the controller
                # can keep communicating with the device.
                self.grbl_monitor.critical(
                    f"serial_io unexpected error: {sys.exc_info()[1]}",
                    exc_info=True,
                )
                time.sleep(0.05)  # avoid tight loop on repeated failures

        self._serial_io_alive = False
        self.grbl_monitor.info(
            f"serial_io thread exiting — reason='{exit_reason}', "
            f"cline_sum={sum(cline)}, pending={len(cline)}"
        )
