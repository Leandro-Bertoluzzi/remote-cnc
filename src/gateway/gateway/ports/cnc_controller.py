"""CncController port — the minimal CNC controller interface.

Any object that implements these methods and attributes is a valid ``CncController``.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class CncController(Protocol):
    """Structural interface for a CNC controller."""

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, port: str, baudrate: int) -> dict[str, str] | None:
        """Open the connection to the CNC device and return startup info."""
        ...

    def disconnect(self) -> None:
        """Close the connection to the CNC device."""
        ...

    def is_io_alive(self) -> bool:
        """Return ``True`` if the serial I/O thread is running."""
        ...

    # ------------------------------------------------------------------
    # Command interface
    # ------------------------------------------------------------------

    def register_ok_hook(self, hook: Optional[Callable[[str], None]]) -> None:
        """Register (or clear with ``None``) a callback for each firmware ``ok``."""
        ...

    def send_command(self, command: str) -> None:
        """Enqueue a G-code line or firmware command for serial transmission."""
        ...

    def set_paused(self, paused: bool) -> None:
        """Issue a feed hold (``True``) or cycle start (``False``)."""
        ...

    def request_soft_reset(self) -> None:
        """Send the soft-reset realtime command."""
        ...

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def query_status_report(self) -> None:
        """Request a status query on the next I/O iteration."""
        ...

    def query_gcode_parser_state(self) -> None:
        """Request a parser-state query."""
        ...

    def query_grbl_settings(self) -> None:
        """Request a settings dump."""
        ...

    def query_grbl_params(self) -> None:
        """Request a parameter dump."""
        ...

    def query_build_info(self) -> None:
        """Request a build-info query."""
        ...

    def query_grbl_help(self) -> None:
        """Request the firmware help message."""
        ...

    # ------------------------------------------------------------------
    # State getters
    # ------------------------------------------------------------------

    def get_buffer_fill(self) -> float:
        """Return the current RX-buffer fill level as a percentage."""
        ...

    def failed(self) -> bool:
        """Return ``True`` if the controller has encountered an error or alarm."""
        ...

    def get_error_message(self) -> Optional[str]:
        """Return the current error message, or ``None`` if there is no error."""
        ...

    def get_status_report(self) -> dict[str, Any]:
        """Return the latest real-time status report as a plain dict."""
        ...

    def get_parser_state(self) -> dict[str, Any]:
        """Return the latest G-code parser state as a plain dict."""
        ...

    def is_connected(self) -> bool:
        """Return ``True`` if the device is currently connected."""
        ...

    def is_paused(self) -> bool:
        """Return ``True`` if the device is in a paused / feed-hold state."""
        ...

    def is_alarm(self) -> bool:
        """Return ``True`` if the device is in ALARM state."""
        ...
