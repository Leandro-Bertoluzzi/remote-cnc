from typing import Callable

from serial import SerialException

from gateway.adapters.cnc.communicator import GrblCommunicator
from gateway.adapters.cnc.constants import GrblCommand
from gateway.adapters.cnc.line_parser import GrblLineParser
from gateway.adapters.cnc.monitor import GrblMonitor
from gateway.adapters.cnc.parsers.grblMsgTypes import (
    GRBL_MSG_FEEDBACK,
    GRBL_MSG_STARTUP,
)
from gateway.application.ports.serial_port import SerialPort

# Type aliases
HomingCallback = Callable[[], None]


class GrblInitializer:
    """Encapsulates the GRBL connection initialization protocol.

    Separating this logic from ``GrblController`` allows:
    - Independent testing of each initialization step.
    - Conditional skipping of the startup-message validation (simulation mode).
    - A clear seam for future extensions (e.g. grblHAL quirks).

    Usage::

        initializer = GrblInitializer(serial, monitor, skip_startup_validation=False)
        startup_payload = initializer.open_connection(port, baudrate, timeout)  # step 1
        initializer.handle_post_startup(communicator)                           # step 2
        initializer.queue_initial_queries(communicator)                         # step 3

    Parameters
    ----------
    serial:
        The ``SerialPort`` adapter (port not yet open).
    monitor:
        A ``GrblMonitor`` for logging.
    skip_startup_validation:
        When ``True``, the ``[MSG_STARTUP]`` validation is skipped so the \
        initializer works with simulators that do not emit the standard Grbl \
        welcome message.  Defaults to ``False``.
    on_homing_required:
        Optional callback invoked when GRBL reports that a homing cycle is \
        required at startup (``[MSG:'$H'|'$X' to unlock]``).
    """

    def __init__(
        self,
        serial: SerialPort,
        monitor: GrblMonitor,
        *,
        skip_startup_validation: bool = False,
        on_homing_required: HomingCallback | None = None,
    ):
        self._serial = serial
        self._monitor = monitor
        self._skip_startup_validation = skip_startup_validation
        self._on_homing_required = on_homing_required

    # ------------------------------------------------------------------
    # Public protocol steps
    # ------------------------------------------------------------------

    def open_connection(self, port: str, baudrate: int, timeout: float) -> dict:
        """Step 1: opens the serial port and validates the GRBL welcome message.

        Calls ``SerialService.startConnection()``, which opens the port *and* reads
        the first non-empty line (the GRBL banner).  The banner is then parsed and
        validated before being returned.

        Returns the parsed startup payload (e.g. ``{'firmware': 'Grbl', 'version': '1.1h', ...}``).

        Raises ``SerialException`` if the port cannot be opened (propagated from \
        ``startConnection`` so the caller can provide a user-facing error message).
        Raises ``Exception`` if the banner message type is unexpected \
        (unless ``skip_startup_validation`` is set).
        """
        # May raise SerialException — intentionally not caught here so the
        # caller can present a meaningful port-level error.
        response = self._serial.startConnection(port, baudrate, timeout)

        msg_type, payload = GrblLineParser.parse(response)
        self._monitor.received(response, msg_type, payload)

        if not self._skip_startup_validation and msg_type != GRBL_MSG_STARTUP:
            self._monitor.critical("Failed starting connection with GRBL")
            raise Exception("Failed starting connection with GRBL: ", payload)

        return payload

    def handle_post_startup(self, communicator: GrblCommunicator) -> None:
        """Step 2: reads the optional post-startup alarm message.

        GRBL may emit ``[MSG:'$H'|'$X' to unlock]`` immediately after the welcome message \
        when an alarm is active. If detected, the ``on_homing_required`` callback is invoked \
        (if provided) and the alarm-disable command is queued.

        Parameters
        ----------
        communicator:
            The ``GrblCommunicator`` (already started or about to start).
            If a homing message is detected and no callback is provided, the ``$X`` command \
            is queued directly.
        """
        try:
            response = self._serial.readLine()
        except SerialException as exc:
            self._monitor.critical(f"Error reading post-startup response from GRBL: {exc}")
            return

        msg_type, payload = GrblLineParser.parse(response)

        if (msg_type == GRBL_MSG_FEEDBACK) and ("$H" in payload.get("message", "")):
            self._monitor.warning("Homing cycle required at startup, handling...")
            if self._on_homing_required:
                self._on_homing_required()
            else:
                # Default: disable alarm
                communicator.send(GrblCommand.DISABLE_ALARM.value)

    def queue_initial_queries(self, communicator: GrblCommunicator) -> None:
        """Step 3: queues the initial information-gathering queries.

        Sends ``$I`` (build info), ``$G`` (parser state) and ``$$`` (settings) so that \
        all controller metadata is available immediately after the connection is established.
        The responses are then handled by the normal flow in ``GrblController``.
        """
        communicator.send(GrblCommand.BUILD.value)
        communicator.send(GrblCommand.PARSER_STATE.value)
        communicator.send(GrblCommand.SETTINGS.value)
        self._monitor.info(
            "Initial queries queued: build info ($I), parser state ($G), settings ($$)"
        )
