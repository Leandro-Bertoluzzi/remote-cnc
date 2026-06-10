"""GatewayClient — Redis-backed adapter for the CNC Gateway.

Implements ``IGatewayClient`` using Redis as key-value store, command queue and PubSub transport.
See DR-0001, DR-0002, DR-0003 for design rationale.

Usage
-----
Production (default config from environment)::

    client = GatewayClient.from_config()

Custom / testing (inject a factory)::

    client = GatewayClient(redis=lambda: FakeRedis())
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

import redis

from core.adapters.gateway.constants import SESSION_TTL_SECONDS
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from core.domain.gateway import (
    ALL_QUEUES,
    EVENTS_CHANNEL,
    GATEWAY_STATE_KEY,
    LAST_STATUS_KEY,
    MSG_COMMAND,
    MSG_DISCONNECT,
    MSG_FILE_START,
    MSG_FILE_STOP,
    MSG_JOG,
    MSG_QUERY,
    MSG_REALTIME,
    QUEUE_CRITICAL,
    QUEUE_HIGH,
    SESSION_KEY,
)
from core.ports.pubsub_client import IPubSub


class GatewayClient:
    """Thin client that pushes commands to the Gateway's Redis queues
    and manages the distributed session lock.

    All methods obtain a fresh connection from the factory on each call,
    which preserves thread-safety without exposing the pool.
    """

    def __init__(self, redis: redis.Redis) -> None:
        self._command_queue = redis
        self._pubsub_client = redis
        self._store = redis

    @classmethod
    def from_config(
        cls,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ) -> "GatewayClient":
        """Build a ``GatewayClient`` backed by a real Redis connection pool."""
        pool = redis.ConnectionPool(host=host, port=port, db=db)
        return cls(redis=redis.Redis(connection_pool=pool))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_message(
        self,
        msg_type: str,
        payload: dict[str, Any],
        session_id: str,
    ) -> str:
        """Serialise a command message for the priority queues."""
        return json.dumps(
            {
                "type": msg_type,
                "payload": payload,
                "session_id": session_id,
                "timestamp": time.time(),
            }
        )

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def acquire_session(
        self,
        user_id: int,
        client_type: str,
        ttl: int = SESSION_TTL_SECONDS,
    ) -> Optional[str]:
        """Try to acquire the CNC session lock.

        Returns the ``session_id`` on success, or ``None`` if the lock
        is already held by another client.
        """
        session_id = uuid.uuid4().hex
        session_data = json.dumps(
            {
                "session_id": session_id,
                "user_id": user_id,
                "client_type": client_type,
                "created_at": time.time(),
            }
        )
        acquired = self._store.set(SESSION_KEY, session_data, nx=True, ex=ttl)
        if not acquired:
            return None
        return session_id

    def renew_session(self, session_id: str, ttl: int = SESSION_TTL_SECONDS) -> bool:
        """Renew the TTL of the session lock (heartbeat).

        Returns ``True`` if the session was renewed, ``False`` if the
        stored session doesn't match (lock lost / expired).
        """
        raw = self._store.get(SESSION_KEY)
        if raw is None:
            return False
        stored = json.loads(raw)
        if stored.get("session_id") != session_id:
            return False
        self._store.expire(SESSION_KEY, ttl)
        return True

    def release_session(self, session_id: str) -> bool:
        """Release the session lock, but only if we own it.

        Uses a Lua script to make the check-and-delete atomic.
        """
        lua = """
        local current = redis.call('GET', KEYS[1])
        if current == false then return 0 end
        local data = cjson.decode(current)
        if data['session_id'] == ARGV[1] then
            redis.call('DEL', KEYS[1])
            return 1
        end
        return 0
        """
        result = self._store.eval(lua, 1, SESSION_KEY, session_id)
        return result == 1

    def get_active_session(self) -> Optional[dict[str, Any]]:
        """Return the current session info, or ``None`` if no active session."""
        raw = self._store.get(SESSION_KEY)
        if raw is None:
            return None
        return json.loads(raw)

    # ------------------------------------------------------------------
    # Command sending
    # ------------------------------------------------------------------

    def send_command(self, session_id: str, command: str) -> None:
        """Send a G-code command with *high* priority."""
        msg = self._make_message(MSG_COMMAND, {"command": command}, session_id)
        self._command_queue.rpush(QUEUE_HIGH, msg)

    def send_jog(
        self,
        session_id: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        feedrate: float = 0,
        *,
        units: Optional[str] = None,
        distance_mode: Optional[str] = None,
        machine_coordinates: bool = False,
    ) -> None:
        """Send a jog command with *high* priority."""
        msg = self._make_message(
            MSG_JOG,
            {
                "x": x,
                "y": y,
                "z": z,
                "feedrate": feedrate,
                "units": units,
                "distance_mode": distance_mode,
                "machine_coordinates": machine_coordinates,
            },
            session_id,
        )
        self._command_queue.rpush(QUEUE_HIGH, msg)

    def send_realtime(self, session_id: str, action: str) -> None:
        """Send a realtime action (pause/resume/stop) with *critical* priority."""
        msg = self._make_message(MSG_REALTIME, {"action": action}, session_id)
        self._command_queue.rpush(QUEUE_CRITICAL, msg)

    def send_query(self, session_id: str, query_type: str) -> None:
        """Send a read-only query with *critical* priority."""
        msg = self._make_message(MSG_QUERY, {"query": query_type}, session_id)
        self._command_queue.rpush(QUEUE_CRITICAL, msg)

    def request_file_execution(
        self,
        session_id: str,
        file_path: str,
        task_id: int | None = None,
        shared_logger_name: str | None = None,
    ) -> None:
        """Request the Gateway to start executing a G-code file.

        - *task_id* may be ``None`` for ad-hoc executions.
        - *shared_logger_name* is the name of the shared logger so the Gateway
        can append to the same log file.
        """
        msg = self._make_message(
            MSG_FILE_START,
            {"file_path": file_path, "task_id": task_id, "shared_logger_name": shared_logger_name},
            session_id,
        )
        self._command_queue.rpush(QUEUE_HIGH, msg)

    def request_file_stop(self, session_id: str) -> None:
        """Request the Gateway to stop the current file execution."""
        msg = self._make_message(MSG_FILE_STOP, {}, session_id)
        self._command_queue.rpush(QUEUE_CRITICAL, msg)

    def request_disconnect(self, session_id: str) -> None:
        """Request the Gateway to release the session (graceful)."""
        msg = self._make_message(MSG_DISCONNECT, {}, session_id)
        self._command_queue.rpush(QUEUE_CRITICAL, msg)

    # ------------------------------------------------------------------
    # Gateway state queries (read-only, no session required)
    # ------------------------------------------------------------------

    def get_gateway_state(self) -> Optional[str]:
        """Return the current gateway state string, or ``None``."""
        raw = self._store.get(GATEWAY_STATE_KEY)
        if raw is None:
            return None
        return raw.decode() if isinstance(raw, bytes) else str(raw)

    def get_last_status(self) -> Optional[dict[str, Any]]:
        """Return the last published status snapshot, or ``None``.

        The CNC Gateway persists the latest status payload in Redis
        so that REST clients can poll without subscribing to PubSub.
        """
        raw = self._store.get(LAST_STATUS_KEY)
        if raw is None:
            return None
        return json.loads(raw)

    def is_gateway_running(self) -> bool:
        """Check if the gateway is publishing state."""
        return self.get_gateway_state() is not None

    def flush_queues(self) -> int:
        """Delete all pending commands from all queues. Returns count deleted."""
        total = 0
        for q in ALL_QUEUES:
            total += self._command_queue.llen(q)
            self._store.delete(q)
        return total

    # ------------------------------------------------------------------
    # Events subscription (for Worker / callers that wait on results)
    # ------------------------------------------------------------------

    def subscribe_events(self) -> IPubSub:
        """Return a PubSub object subscribed to the events channel."""
        return self.subscribe_channels(EVENTS_CHANNEL)

    def subscribe_channels(self, *channels: str) -> IPubSub:
        """Return a PubSub object subscribed to one or more channels."""
        ps = self._pubsub_client.pubsub()
        ps.subscribe(*channels)
        return ps
