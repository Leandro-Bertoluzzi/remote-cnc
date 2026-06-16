"""Status publisher for the CNC Gateway.

Periodically reads CNC state from the controller and publishes a
unified JSON payload to the status PubSub channel.

It also stores the latest snapshot in the key-value store.

The payload format is designed so that **all** consumers receive the
same data structure regardless of gateway mode.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from core.domain.gateway import GATEWAY_STATE_KEY, GW_STATE_IDLE, LAST_STATUS_KEY, STATUS_CHANNEL
from core.ports.key_value_store import IKeyValueStore
from core.ports.pubsub_client import IPubSubClient

from gateway.application.ports.cnc_controller import CncController

if TYPE_CHECKING:
    from gateway.application.file_executor import FileExecutor
    from gateway.application.session_manager import SessionManager

# How often to publish status (seconds)
STATUS_INTERVAL = 0.10


class StatusPublisher:
    """Reads CNC controller state, publishes to PubSub and stores snapshots in key-value store."""

    def __init__(
        self,
        controller: CncController,
        session_manager: SessionManager,
        file_executor: FileExecutor,
        store: IKeyValueStore,
        pubsub_client: IPubSubClient,
    ):
        self.controller = controller
        self.session_manager = session_manager
        self.file_executor = file_executor
        self._store = store
        self._pubsub_client = pubsub_client
        self._last_publish = 0.0
        self._gateway_state = GW_STATE_IDLE

    @property
    def gateway_state(self) -> str:
        return self._gateway_state

    @gateway_state.setter
    def gateway_state(self, value: str) -> None:
        self._gateway_state = value
        self._store.set(GATEWAY_STATE_KEY, value)

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
        """Remove the gateway state keys from the store on shutdown."""
        self._store.delete(GATEWAY_STATE_KEY)
        self._store.delete(LAST_STATUS_KEY)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _publish_status(self) -> None:
        session = self.session_manager.get_active_session()

        payload: dict[str, Any] = {
            "status": self.controller.get_status_report(),
            "parserstate": self.controller.get_parser_state(),
            "gateway_state": self._gateway_state,
            "session": session,
            "file_progress": None,
        }

        if self.file_executor.is_running:
            payload["file_progress"] = self.file_executor.get_progress()

        message = json.dumps(payload, default=str)
        self._pubsub_client.publish(STATUS_CHANNEL, message)
        # Persist snapshot for polling
        self._store.set(LAST_STATUS_KEY, message)
