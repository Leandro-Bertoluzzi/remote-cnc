"""Session manager for the CNC Gateway.

Validates incoming commands against the active session and publishes
session lifecycle events.

The distributed lock itself lives in the key-value store and is managed by `GatewayClient`.
This module provides the *server-side* validation that runs inside the Gateway process.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from core.domain.gateway import (
    EVENT_SESSION_ACQUIRED,
    EVENT_SESSION_RELEASED,
    EVENTS_CHANNEL,
    SESSION_KEY,
)
from core.ports.key_value_store import IKeyValueStore
from core.ports.pubsub_client import IPubSubClient

logger = logging.getLogger(__name__)


class SessionManager:
    """Server-side session validation for the Gateway process."""

    def __init__(self, pubsub_client: IPubSubClient, store: IKeyValueStore):
        self._pubsub_client = pubsub_client
        self._store = store

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def get_active_session(self) -> Optional[dict[str, Any]]:
        """Read and decode the current session from the key-value store."""
        raw = self._store.get(SESSION_KEY)
        if raw is None:
            return None
        return json.loads(raw)

    def validate_session(self, session_id: str) -> bool:
        """Return ``True`` if *session_id* matches the active session."""
        session = self.get_active_session()
        if session is None:
            return False
        return session.get("session_id") == session_id

    def has_active_session(self) -> bool:
        """Check if there is any active session."""
        return self._store.exists(SESSION_KEY) == 1

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def publish_session_acquired(self, session_data: dict[str, Any]) -> None:
        """Publish a session-acquired event on the events channel."""
        event = json.dumps({"type": EVENT_SESSION_ACQUIRED, "session": session_data})
        self._pubsub_client.publish(EVENTS_CHANNEL, event)
        logger.info(
            "Session acquired by user %s (%s)",
            session_data.get("user_id"),
            session_data.get("client_type"),
        )

    def publish_session_released(self, session_id: str) -> None:
        """Publish a session-released event on the events channel."""
        event = json.dumps({"type": EVENT_SESSION_RELEASED, "session_id": session_id})
        self._pubsub_client.publish(EVENTS_CHANNEL, event)
        logger.info("Session %s released", session_id[:8])
