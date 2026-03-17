"""Session manager for the CNC Gateway.

Validates incoming commands against the active session and publishes
session lifecycle events.

The distributed lock itself lives in Redis and is managed by `GatewayClient`.
This module provides the *server-side* validation that runs inside the
Gateway process.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from core.utilities.gateway.constants import (
    EVENT_SESSION_ACQUIRED,
    EVENT_SESSION_RELEASED,
    EVENTS_CHANNEL,
    SESSION_KEY,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Server-side session validation for the Gateway process."""

    def __init__(
        self,
        redis_conn: redis.Redis | None = None,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self._redis: redis.Redis[bytes]
        if redis_conn is not None:
            self._redis = redis_conn
        else:
            self._redis = redis.Redis(host=host, port=port, db=db)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def get_active_session(self) -> Optional[dict[str, Any]]:
        """Read and decode the current session from Redis."""
        raw = self._redis.get(SESSION_KEY)
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
        return self._redis.exists(SESSION_KEY) == 1

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def publish_session_acquired(self, session_data: dict[str, Any]) -> None:
        """Publish a session-acquired event on the events channel."""
        event = json.dumps({"type": EVENT_SESSION_ACQUIRED, "session": session_data})
        self._redis.publish(EVENTS_CHANNEL, event)
        logger.info(
            "Session acquired by user %s (%s)",
            session_data.get("user_id"),
            session_data.get("client_type"),
        )

    def publish_session_released(self, session_id: str) -> None:
        """Publish a session-released event on the events channel."""
        event = json.dumps({"type": EVENT_SESSION_RELEASED, "session_id": session_id})
        self._redis.publish(EVENTS_CHANNEL, event)
        logger.info("Session %s released", session_id[:8])
