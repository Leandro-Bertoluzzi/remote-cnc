import re
import sys
import threading
import time
from queue import Empty, Queue
from typing import TYPE_CHECKING, Callable, Optional

from serial import SerialException

from core.utilities.gcode.constants import GCODE_PROGRAM_END_CODES
from core.utilities.grbl.constants import GrblRealtimeCommand
from core.utilities.grbl.grblLineParser import GrblLineParser
from core.utilities.grbl.grblStatus import GrblStatus, GrblStatusFlag
from core.utilities.grbl.parsers.grblMsgTypes import (
    GRBL_MSG_ALARM,
    GRBL_RESULT_ERROR,
    GRBL_RESULT_OK,
)
from core.utilities.serial import SerialService

if TYPE_CHECKING:
    from core.utilities.grbl.grblMonitor import GrblMonitor

# Type aliases
OnOkCallback = Callable[[str], None]
OnErrorCallback = Callable[[str, dict], None]
OnAlarmCallback = Callable[[str, dict], None]
OnMessageCallback = Callable[[str | None, dict], None]
OnProgramEndCallback = Callable[[], None]
OnDisconnectCallback = Callable[[], None]

# Constants
RX_BUFFER_SIZE = 128

# Commands that write to GRBL's EEPROM.  Sending a subsequent command before
# the EEPROM write completes can corrupt the internal state, so
# GrblCommunicator temporarily enforces single-step mode for these.
_EEPROM_PATTERN = re.compile(
    r"G10|G28\.1|G30\.1|G5[4-9]|\$[0-9]+=|\$I|\$N|\$RST=|\$\$|\$#",
    re.IGNORECASE,
)

# Query commands that are safe to send in any controller state (including paused/error).
GRBL_QUERY_COMMANDS = {"$G", "$$", "$#", "$I", "$N"}


class GrblCommunicator:
    """Handles all raw serial I/O with the GRBL device.

    Responsibilities:
    - Managing the ``serial_io`` thread lifecycle.
    - Maintaining the GRBL RX buffer accounting (``cline``/``sline``/``_sumcline``).
    - Enforcing single-step mode for EEPROM-writing commands.
    - Parsing every line received from GRBL and dispatching to semantic callbacks.
    - Exposing ``send``, ``send_realtime`` and ``empty_queue``.

    Callbacks (all invoked from the I/O thread):

    - ``on_ok(done_cmd)``        — called when GRBL acknowledges a command with ``ok``.
    - ``on_error(line, payload)`` — called on ``error:N``; buffer has already been cleared.
    - ``on_alarm(line, payload)`` — called on ``ALARM:N``; buffer has already been cleared.
    - ``on_message(msg_type, payload)`` — called for all other message types.
    - ``on_program_end()``       — called when a program-end G-code (M2/M30) is sent.
    - ``on_disconnect()``        — called when the I/O thread exits due to a serial error.
    """

    def __init__(
        self,
        serial: SerialService,
        grbl_status: GrblStatus,
        monitor: "GrblMonitor",
        *,
        on_ok: OnOkCallback,
        on_error: OnErrorCallback,
        on_alarm: OnAlarmCallback,
        on_message: OnMessageCallback,
        on_program_end: OnProgramEndCallback,
        on_disconnect: OnDisconnectCallback,
    ):
        self._serial = serial
        self._grbl_status = grbl_status
        self._monitor = monitor

        # Callbacks
        self._on_ok = on_ok
        self._on_error = on_error
        self._on_alarm = on_alarm
        self._on_message = on_message
        self._on_program_end = on_program_end
        self._on_disconnect = on_disconnect

        # Threading
        self._thread: Optional[threading.Thread] = None

        # Buffer tracking
        self._sumcline: int = 0  # current byte-count in GRBL RX buffer
        self._status_query_pending: bool = False

        # Command queue
        self.queue: Queue[str] = Queue()

        # Single-step mode support (for EEPROM commands)
        self._single_step: bool = False
        self._temporary_single_step: bool = False

        # Public read-only flag
        self.alive: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Starts the I/O thread."""
        self._thread = threading.Thread(target=self._serial_io, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signals the I/O thread to stop on its next iteration."""
        self._thread = None

    def send(self, command: str) -> None:
        """Enqueues a command for transmission."""
        self.queue.put(command)

    def send_realtime(self, cmd: bytes, label: str) -> None:
        """Sends a real-time command directly to the serial port."""
        try:
            self._serial.sendBytes(cmd)
        except SerialException as e:
            self._monitor.error(f"Error sending {label}: {e}")
            return
        cmd_str = repr(cmd)[2:-1]
        self._monitor.sent(cmd_str)
        self._monitor.info(f"Requested {label}")

    def request_status_query(self) -> None:
        """Schedules a ``?`` query to be sent from the I/O thread."""
        self._status_query_pending = True

    def empty_queue(self) -> None:
        """Drains the command queue."""
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except Empty:
                break

    def get_buffer_fill(self) -> float:
        """Returns the GRBL RX buffer fill as a percentage."""
        return self._sumcline * 100.0 / RX_BUFFER_SIZE

    # ------------------------------------------------------------------
    # Single-step mode
    # ------------------------------------------------------------------

    def _is_eeprom_command(self, command: str) -> bool:
        return bool(_EEPROM_PATTERN.search(command))

    def _enter_single_step_if_needed(self, command: str) -> None:
        if self._is_eeprom_command(command):
            if not self._single_step:
                self._temporary_single_step = True
                self._single_step = True
        elif self._temporary_single_step:
            self._temporary_single_step = False
            self._single_step = False

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------

    def _handle_response(self, response: str, cline: list[int], sline: list[str]) -> None:
        """Parse a line from GRBL, update buffer accounting, and dispatch to the \
        appropriate semantic callback.

        This method is the single point responsible for:
        - Calling ``GrblLineParser.parse``.
        - Draining ``cline``/``sline`` on ``ok``, ``error``, and ``ALARM``.
        - Maintaining ``_sumcline`` to mirror the GRBL RX buffer fill level.
        - Setting low-level status flags (ALARM, PAUSED) for ``ALARM`` responses.
        - Emptying the send queue on ``error`` / ``ALARM`` (stale commands will \
          never be acknowledged by GRBL after these events).
        """
        try:
            msg_type, payload = GrblLineParser.parse(response)
        except Exception as error:
            self._monitor.error(
                f"Error parsing response from GRBL.\nResponse: {response}\nError: {str(error)}"
            )
            return
        self._monitor.received(response, msg_type, payload)

        if msg_type == GRBL_RESULT_OK:
            done_cmd = sline.pop(0) if sline else ""
            if cline:
                del cline[0]
            self._sumcline = sum(cline)
            self._on_ok(done_cmd)
            return

        if msg_type == GRBL_RESULT_ERROR:
            # GRBL discards all buffered commands on error.
            error_line = sline.pop(0) if sline else ""
            cline.clear()
            sline.clear()
            self._sumcline = 0
            self.empty_queue()
            payload.pop("raw", None)
            self._on_error(error_line, payload)
            return

        if msg_type == GRBL_MSG_ALARM:
            # GRBL abandons all buffered commands on alarm.
            alarm_line = sline.pop(0) if sline else ""
            cline.clear()
            sline.clear()
            self._sumcline = 0
            self.empty_queue()
            payload.pop("raw", None)
            self._on_alarm(alarm_line, payload)
            return

        # All other message types — strip internal field and forward.
        payload.pop("raw", None)
        self._on_message(msg_type, payload)

    def _serial_io(self) -> None:
        """Thread performing I/O on the serial line.

        Responsible only for:
        - Dequeuing commands from the internal queue.
        - Tracking the GRBL RX buffer via ``cline``.
        - Sending commands over serial when buffer space is available.
        - Reading GRBL responses and dispatching them via ``_handle_response``.
        - Handling stop requests and program-end codes.
        """
        cline: list[int] = []
        sline: list[str] = []
        tosend: Optional[str] = None
        exit_reason = "loop ended (thread set to None)"

        self.alive = True
        self._monitor.info("serial_io thread started")

        while self._thread:
            try:
                # ── Status query ─────────────────────────────────────────────
                if self._status_query_pending:
                    try:
                        self._serial.sendBytes(GrblRealtimeCommand.STATUS_REPORT.value)
                        self._monitor.sent("?", debug=True)
                    except SerialException as e:
                        self._monitor.error(f"Error sending STATUS: {e}")
                    finally:
                        self._status_query_pending = False
                    continue

                # ── Dequeue next command ──────────────────────────────────────
                # Skip dequeue when in single-step mode and the previous EEPROM command
                # has not yet been acknowledged (cline is non-empty). This prevents
                # sending a subsequent command before the EEPROM write completes.
                if (
                    tosend is None
                    and self.queue.qsize() > 0
                    and not (self._single_step and len(cline) > 0)
                ):
                    next_cmd = self.queue.queue[0]  # peek
                    if not self._grbl_status.paused() or next_cmd in GRBL_QUERY_COMMANDS:
                        try:
                            tosend = self.queue.get_nowait()
                        except Empty:
                            continue

                    if tosend is not None:
                        self._enter_single_step_if_needed(tosend)
                        sline.append(tosend)
                        cline.append(len(tosend) + 1)  # +1 for '\n'

                # ── Receive ───────────────────────────────────────────────────
                if self._serial.waiting() or tosend is None:
                    try:
                        response = self._serial.readLine()
                    except SerialException:
                        self._monitor.error(
                            f"Error reading response from GRBL: {str(sys.exc_info()[1])}"
                        )
                        self.empty_queue()
                        self.alive = False
                        self._on_disconnect()
                        exit_reason = "SerialException on read"
                        return

                    if response:
                        self._handle_response(response, cline, sline)

                # ── Stop request ──────────────────────────────────────────────
                if self._grbl_status.get_flag(GrblStatusFlag.STOP.value):
                    self.empty_queue()
                    tosend = None
                    self._grbl_status.set_flag(GrblStatusFlag.STOP.value, False)
                    self._monitor.info("STOP request processed")

                # ── Send ──────────────────────────────────────────────────────
                if tosend is not None and sum(cline) < RX_BUFFER_SIZE:
                    self._sumcline = sum(cline)
                    try:
                        self._serial.sendLine(tosend)
                    except SerialException:
                        self._monitor.error(
                            f"Error sending command to GRBL: {str(sys.exc_info()[1])}"
                        )
                        error_data = {
                            "code": 0,
                            "message": "Communication error",
                            "description": str(sys.exc_info()[1]),
                        }
                        self._grbl_status.set_error(tosend, error_data)
                        self.empty_queue()
                        self.alive = False
                        self._on_disconnect()
                        exit_reason = "SerialException on write"
                        return

                    self._monitor.sent(tosend)
                    self._monitor.debug(
                        f"[Buffer] Sent '{tosend}', "
                        f"cline_sum={self._sumcline}/{RX_BUFFER_SIZE}, pending={len(cline)}"
                    )

                    if tosend.strip() in GCODE_PROGRAM_END_CODES:
                        self._monitor.info(f"A program end command was found: {tosend}")
                        self._grbl_status.set_flag(GrblStatusFlag.FINISHED.value, True)
                        self.empty_queue()
                        self._on_program_end()
                        exit_reason = "program end command"
                        break

                    tosend = None

                elif tosend is not None:
                    self._monitor.debug(
                        f"[Buffer] Full — waiting to send '{tosend}', "
                        f"cline_sum={sum(cline)}/{RX_BUFFER_SIZE}, pending={len(cline)}"
                    )

            except Exception:
                self._monitor.critical(
                    f"serial_io unexpected error: {sys.exc_info()[1]}",
                    exc_info=True,
                )
                time.sleep(0.05)

        self.alive = False
        self._monitor.info(
            f"serial_io thread exiting — reason='{exit_reason}', "
            f"cline_sum={sum(cline)}, pending={len(cline)}"
        )
