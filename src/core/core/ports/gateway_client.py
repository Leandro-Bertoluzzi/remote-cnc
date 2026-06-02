"""IGatewayClient port — the interface for communicating with the CNC Gateway."""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from core.ports.pubsub_client import IPubSub


@runtime_checkable
class IGatewayClient(Protocol):
    """Structural interface for a CNC Gateway client."""

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def acquire_session(
        self,
        user_id: int,
        client_type: str,
        ttl: int = ...,
    ) -> Optional[str]:
        """Try to acquire the CNC session lock.

        Returns the ``session_id`` on success, or ``None`` if already held.
        """
        ...

    def renew_session(self, session_id: str, ttl: int = ...) -> bool:
        """Renew the TTL on the session lock. Returns ``False`` if lost."""
        ...

    def release_session(self, session_id: str) -> bool:
        """Release the session lock atomically. Returns ``True`` if released."""
        ...

    def get_active_session(self) -> Optional[dict[str, Any]]:
        """Return the current session info, or ``None``."""
        ...

    # ------------------------------------------------------------------
    # Command sending
    # ------------------------------------------------------------------

    def send_command(self, session_id: str, command: str) -> None:
        """Send a G-code command."""
        ...

    def send_jog(
        self,
        session_id: str,
        x: float = ...,
        y: float = ...,
        z: float = ...,
        feedrate: float = ...,
        *,
        units: Optional[str] = ...,
        distance_mode: Optional[str] = ...,
        machine_coordinates: bool = ...,
    ) -> None:
        """Send a jog command."""
        ...

    def send_realtime(self, session_id: str, action: str) -> None:
        """Send a realtime action (pause / resume / stop / soft_reset)."""
        ...

    def send_query(self, session_id: str, query_type: str) -> None:
        """Send a read-only query."""
        ...

    def request_file_execution(
        self,
        session_id: str,
        file_path: str,
        task_id: int | None = ...,
    ) -> None:
        """Request the Gateway to start executing a G-code file."""
        ...

    def request_file_stop(self, session_id: str) -> None:
        """Request the Gateway to stop the current file execution."""
        ...

    def request_disconnect(self, session_id: str) -> None:
        """Request the Gateway to release the session (graceful)."""
        ...

    # ------------------------------------------------------------------
    # Gateway state queries (no session required)
    # ------------------------------------------------------------------

    def get_gateway_state(self) -> Optional[str]:
        """Return the current gateway state string, or ``None``."""
        ...

    def get_last_status(self) -> Optional[dict[str, Any]]:
        """Return the last published status snapshot, or ``None``."""
        ...

    def is_gateway_running(self) -> bool:
        """Check if the gateway is publishing state."""
        ...

    def flush_queues(self) -> int:
        """Delete all pending commands from all queues."""
        ...

    # ------------------------------------------------------------------
    # Events subscription
    # ------------------------------------------------------------------

    def subscribe_events(self) -> IPubSub:
        """Return a PubSub subscribed to the events channel."""
        ...

    def subscribe_channels(self, *channels: str) -> IPubSub:
        """Return a PubSub subscribed to one or more channels."""
        ...
