"""Tests for GatewayClient."""

from __future__ import annotations

import json
from typing import Any, cast

import fakeredis
import pytest
from core.adapters.gateway.gateway_client import GatewayClient
from core.domain.gateway import (
    ALL_QUEUES,
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

# ---------------------------------------------------------------------------
# FakeRedis with Lua eval support
# ---------------------------------------------------------------------------


class FakeRedisWithLua(fakeredis.FakeRedis):
    """FakeRedis extended with a functional ``eval`` for the release-session Lua script.

    Rather than emulating a full Lua runtime, this class replaces ``eval``
    with a Python equivalent that has identical semantics: atomic
    compare-and-delete on a JSON-encoded session key.
    """

    def eval(self, script: str, numkeys: int, *keys_and_args: Any) -> Any:
        key = keys_and_args[0]
        session_id = keys_and_args[1]
        raw = self.get(key)
        if raw is None:
            return 0
        data = json.loads(cast(bytes, raw))
        if data.get("session_id") == session_id:
            self.delete(key)
            return 1
        return 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis() -> FakeRedisWithLua:
    """Isolated in-memory Redis instance shared within a test."""
    return FakeRedisWithLua()


@pytest.fixture()
def client(fake_redis: FakeRedisWithLua) -> GatewayClient:
    """A GatewayClient backed by ``fake_redis``."""
    return GatewayClient(redis_factory=lambda: fake_redis)


@pytest.fixture()
def redis(fake_redis: FakeRedisWithLua) -> FakeRedisWithLua:
    """Expose the raw FakeRedis instance for assertion helpers."""
    return fake_redis


def _pop_message(r: Any, queue: str) -> dict:
    """LPOP a message from *queue* and deserialise it."""
    raw = r.lpop(queue)
    assert raw is not None, f"Expected a message in {queue!r} but queue is empty"
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    def test_acquire_session_returns_session_id(self, client, redis):
        sid = client.acquire_session(user_id=1, client_type="desktop")
        assert sid is not None
        stored = json.loads(redis.get(SESSION_KEY))
        assert stored["session_id"] == sid
        assert stored["user_id"] == 1
        assert stored["client_type"] == "desktop"

    def test_acquire_session_fails_when_lock_held(self, client):
        sid1 = client.acquire_session(user_id=1, client_type="desktop")
        sid2 = client.acquire_session(user_id=2, client_type="worker")
        assert sid1 is not None
        assert sid2 is None

    def test_renew_session_returns_true_for_owner(self, client):
        sid = client.acquire_session(user_id=1, client_type="desktop")
        assert client.renew_session(sid) is True

    def test_renew_session_returns_false_for_wrong_id(self, client):
        client.acquire_session(user_id=1, client_type="desktop")
        assert client.renew_session("wrong-id") is False

    def test_renew_session_returns_false_when_no_session(self, client):
        assert client.renew_session("any-id") is False

    def test_release_session_removes_key(self, client, redis):
        sid = client.acquire_session(user_id=1, client_type="desktop")
        assert client.release_session(sid) is True
        assert redis.get(SESSION_KEY) is None

    def test_release_session_rejects_wrong_id(self, client, redis):
        client.acquire_session(user_id=1, client_type="desktop")
        assert client.release_session("wrong-id") is False
        assert redis.get(SESSION_KEY) is not None  # still held

    def test_get_active_session_returns_data(self, client):
        sid = client.acquire_session(user_id=1, client_type="worker")
        session = client.get_active_session()
        assert session is not None
        assert session["session_id"] == sid

    def test_get_active_session_returns_none_when_empty(self, client):
        assert client.get_active_session() is None


# ---------------------------------------------------------------------------
# Command queues
# ---------------------------------------------------------------------------


class TestCommandQueues:
    def test_send_command_pushes_to_high_queue(self, client, redis):
        client.send_command("sid", "G0 X10")
        msg = _pop_message(redis, QUEUE_HIGH)
        assert msg["type"] == MSG_COMMAND
        assert msg["payload"]["command"] == "G0 X10"
        assert msg["session_id"] == "sid"

    def test_send_jog_pushes_to_high_queue(self, client, redis):
        client.send_jog("sid", x=5, y=0, z=-2, feedrate=1000)
        msg = _pop_message(redis, QUEUE_HIGH)
        assert msg["type"] == MSG_JOG
        assert msg["payload"]["x"] == 5
        assert msg["payload"]["z"] == -2
        assert msg["payload"]["feedrate"] == 1000

    def test_send_realtime_pushes_to_critical_queue(self, client, redis):
        client.send_realtime("sid", "pause")
        msg = _pop_message(redis, QUEUE_CRITICAL)
        assert msg["type"] == MSG_REALTIME
        assert msg["payload"]["action"] == "pause"

    def test_send_query_pushes_to_critical_queue(self, client, redis):
        client.send_query("sid", "status")
        msg = _pop_message(redis, QUEUE_CRITICAL)
        assert msg["type"] == MSG_QUERY
        assert msg["payload"]["query"] == "status"

    def test_request_file_execution_pushes_to_high_queue(self, client, redis):
        client.request_file_execution("sid", "/path/to/file.gcode", task_id=42)
        msg = _pop_message(redis, QUEUE_HIGH)
        assert msg["type"] == MSG_FILE_START
        assert msg["payload"]["file_path"] == "/path/to/file.gcode"
        assert msg["payload"]["task_id"] == 42

    def test_request_file_execution_without_task_id(self, client, redis):
        client.request_file_execution("sid", "/path/to/file.gcode")
        msg = _pop_message(redis, QUEUE_HIGH)
        assert msg["payload"]["task_id"] is None

    def test_request_file_stop_pushes_to_critical_queue(self, client, redis):
        client.request_file_stop("sid")
        msg = _pop_message(redis, QUEUE_CRITICAL)
        assert msg["type"] == MSG_FILE_STOP

    def test_request_disconnect_pushes_to_critical_queue(self, client, redis):
        client.request_disconnect("sid")
        msg = _pop_message(redis, QUEUE_CRITICAL)
        assert msg["type"] == MSG_DISCONNECT


# ---------------------------------------------------------------------------
# Message format
# ---------------------------------------------------------------------------


class TestMessageFormat:
    def test_message_contains_required_fields(self, client, redis):
        client.send_command("my-session", "G28")
        msg = _pop_message(redis, QUEUE_HIGH)
        assert "type" in msg
        assert "payload" in msg
        assert "session_id" in msg
        assert "timestamp" in msg
        assert msg["session_id"] == "my-session"
        assert isinstance(msg["timestamp"], float)


# ---------------------------------------------------------------------------
# Gateway state queries
# ---------------------------------------------------------------------------


class TestGatewayStateQueries:
    def test_get_gateway_state_returns_none_when_missing(self, client):
        assert client.get_gateway_state() is None

    def test_is_gateway_running_false_when_no_state(self, client):
        assert client.is_gateway_running() is False

    def test_get_gateway_state_returns_value(self, client, redis):
        redis.set(GATEWAY_STATE_KEY, "idle")
        assert client.get_gateway_state() == "idle"

    def test_is_gateway_running_true_when_state_present(self, client, redis):
        redis.set(GATEWAY_STATE_KEY, "streaming")
        assert client.is_gateway_running() is True

    def test_get_last_status_returns_none_when_missing(self, client):
        assert client.get_last_status() is None

    def test_get_last_status_returns_parsed_json(self, client, redis):
        payload = {"activeState": "Idle", "mpos": {"x": 0, "y": 0, "z": 0}}
        redis.set(LAST_STATUS_KEY, json.dumps(payload))
        result = client.get_last_status()
        assert result == payload

    def test_flush_queues_clears_all_queues(self, client, redis):
        client.send_command("sid", "G0 X10")
        client.send_realtime("sid", "pause")
        count = client.flush_queues()
        assert count >= 2
        for q in ALL_QUEUES:
            assert redis.llen(q) == 0
