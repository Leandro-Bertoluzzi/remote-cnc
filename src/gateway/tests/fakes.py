"""Shared fake implementations of gateway ports for use in unit tests."""

from __future__ import annotations

from typing import Any, Callable, Optional
from unittest.mock import MagicMock

from core.domain.cnc import JogDistanceMode, JogUnit
from gateway.fileExecutor import FileExecutor


class FakeController:
    """In-memory implementation of the ``CncController`` Protocol for unit tests.

    All methods that have side-effects (commands, queries) delegate to a
    corresponding ``*_mock`` attribute so tests can assert call counts and args.

    Attributes
    ----------
    status_report:
        Value returned by ``get_status_report()``.
    parser_state:
        Value returned by ``get_parser_state()``.
    buffer_fill:
        Value returned by ``get_buffer_fill()``.
    is_failed:
        Value returned by ``failed()``.
    error_message:
        Value returned by ``get_error_message()``.
    """

    def __init__(
        self,
        *,
        buffer_fill: float = 0.0,
        status_failed: bool = False,
        error_message: Optional[str] = None,
        status_report: Optional[dict] = None,
        parser_state: Optional[dict] = None,
    ):
        self._failed = status_failed
        self._error_message = error_message
        self._buffer_fill = buffer_fill
        self._ok_hook: Optional[Callable[[str], None]] = None
        self.status_report: dict = status_report or {}
        self.parser_state: dict = parser_state or {}

        # Spy mocks — tests assert on these
        self.send_command_mock = MagicMock()
        self.jog_mock = MagicMock()
        self.set_paused_mock = MagicMock()
        self.request_soft_reset_mock = MagicMock()
        self.query_status_report_mock = MagicMock()
        self.query_gcode_parser_state_mock = MagicMock()
        self.query_grbl_settings_mock = MagicMock()
        self.query_grbl_params_mock = MagicMock()
        self.query_build_info_mock = MagicMock()
        self.query_grbl_help_mock = MagicMock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, port: str, baudrate: int) -> dict[str, str] | None:
        return None

    def disconnect(self) -> None:
        pass

    def is_io_alive(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Command interface
    # ------------------------------------------------------------------

    def register_ok_hook(self, hook: Optional[Callable[[str], None]]) -> None:
        self._ok_hook = hook

    def send_command(self, command: str) -> None:
        self.send_command_mock(command)

    def set_paused(self, paused: bool) -> None:
        self.set_paused_mock(paused)

    def request_soft_reset(self) -> None:
        self.request_soft_reset_mock()

    def jog(
        self,
        x: float,
        y: float,
        z: float,
        feedrate: float,
        *,
        units: JogUnit | None = None,
        distance_mode: JogDistanceMode | None = None,
        machine_coordinates: bool = False,
    ) -> None:
        self.jog_mock(
            x,
            y,
            z,
            feedrate,
            units=units,
            distance_mode=distance_mode,
            machine_coordinates=machine_coordinates,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def query_status_report(self) -> None:
        self.query_status_report_mock()

    def query_gcode_parser_state(self) -> None:
        self.query_gcode_parser_state_mock()

    def query_grbl_settings(self) -> None:
        self.query_grbl_settings_mock()

    def query_grbl_params(self) -> None:
        self.query_grbl_params_mock()

    def query_build_info(self) -> None:
        self.query_build_info_mock()

    def query_grbl_help(self) -> None:
        self.query_grbl_help_mock()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def get_buffer_fill(self) -> float:
        return self._buffer_fill

    def failed(self) -> bool:
        return self._failed

    def get_error_message(self) -> Optional[str]:
        return self._error_message

    def get_status_report(self) -> dict[str, Any]:
        return self.status_report

    def get_parser_state(self) -> dict[str, Any]:
        return self.parser_state

    def is_connected(self) -> bool:
        return True

    def is_paused(self) -> bool:
        return False

    def is_alarm(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Convenience helpers for tests
    # ------------------------------------------------------------------

    def fire_ok(self, done_cmd: str = "G0 X10") -> None:
        """Simulate a GRBL ``ok`` response for the given command."""
        if self._ok_hook:
            self._ok_hook(done_cmd)


class FakeFileExecutor(FileExecutor):
    """Subclass of ``FileExecutor`` with all side-effectful methods replaced by spies.

    Constructed with a ``FakeController`` and a ``MagicMock`` Redis client so
    that no real serial or Redis connections are needed.
    """

    def __init__(self, *, running: bool = False):
        super().__init__(FakeController(), redis_conn=MagicMock())
        self._running = running

        # Replace methods with spies after super().__init__()
        self.start = MagicMock()  # type: ignore[method-assign]
        self.stop = MagicMock()  # type: ignore[method-assign]
        self.pause = MagicMock()  # type: ignore[method-assign]
        self.resume = MagicMock()  # type: ignore[method-assign]
        self.get_progress = MagicMock(return_value={})  # type: ignore[method-assign]


class FakeSessionManager:
    """Minimal stub for ``SessionManager`` used in StatusPublisher/CommandProcessor tests."""

    def __init__(
        self,
        *,
        active_session: Optional[dict[str, Any]] = None,
        session_valid: bool = True,
    ):
        self._active_session = active_session
        self._session_valid = session_valid

    def get_active_session(self) -> Optional[dict[str, Any]]:
        return self._active_session

    def validate_session(self, session_id: str) -> bool:
        if self._active_session is None:
            return False
        return self._session_valid

    def has_active_session(self) -> bool:
        return self._active_session is not None
