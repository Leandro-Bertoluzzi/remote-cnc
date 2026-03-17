"""Status publisher for the CNC Gateway.

Periodically reads CNC state from the GrblController and publishes a
unified JSON payload to the ``grbl_status`` Redis PubSub channel.

The payload format is designed so that **all** consumers receive the
same data structure regardless of gateway mode.
"""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

import redis
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from core.utilities.gateway.constants import (
    GATEWAY_STATE_KEY,
    GW_STATE_IDLE,
    STATUS_CHANNEL,
)

if TYPE_CHECKING:
    from core.utilities.grbl.grblController import GrblController

    from gateway.fileExecutor import FileExecutor
    from gateway.sessionManager import SessionManager

logger = logging.getLogger(__name__)

# How often to publish status (seconds)
STATUS_INTERVAL = 0.10


class StatusPublisher:
    """Reads GrblController state and publishes to Redis PubSub."""

    def __init__(
        self,
        controller: GrblController,
        session_manager: SessionManager,
        file_executor: FileExecutor,
        redis_conn: redis.Redis | None = None,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self.controller = controller
        self.session_manager = session_manager
        self.file_executor = file_executor
        self._redis = (
            redis_conn if redis_conn is not None else redis.Redis(host=host, port=port, db=db)
        )
        self._last_publish = 0.0
        self._gateway_state = GW_STATE_IDLE

    @property
    def gateway_state(self) -> str:
        return self._gateway_state

    @gateway_state.setter
    def gateway_state(self, value: str) -> None:
        self._gateway_state = value
        self._redis.set(GATEWAY_STATE_KEY, value)

    def publish_if_due(self) -> bool:
        """Publish a status update if enough time has elapsed.

        Returns ``True`` if a message was published.
        """
        now = time.time()
        if now - self._last_publish < STATUS_INTERVAL:
            return False

        self._publish_status()
        self._last_publish = now
        return True

    def publish_now(self) -> None:
        """Force an immediate status publish (e.g. after an event)."""
        self._publish_status()
        self._last_publish = time.time()

    def cleanup(self) -> None:
        """Remove the gateway state key from Redis on shutdown."""
        self._redis.delete(GATEWAY_STATE_KEY)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish_status(self) -> None:
        status = self.controller.grbl_status
        session = self.session_manager.get_active_session()

        payload: dict[str, Any] = {
            "status": status.get_status_report(),
            "parserstate": status.get_parser_state(),
            "gateway_state": self._gateway_state,
            "session": session,
            "file_progress": None,
        }

        if self.file_executor.is_running:
            payload["file_progress"] = self.file_executor.get_progress()

        message = json.dumps(payload, default=str)
        self._redis.publish(STATUS_CHANNEL, message)
