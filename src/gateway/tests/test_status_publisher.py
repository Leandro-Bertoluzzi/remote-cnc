"""Tests for gateway.StatusPublisher."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from core.domain.gateway import (
    GATEWAY_STATE_KEY,
    GW_STATE_IDLE,
    GW_STATE_STREAMING,
    LAST_STATUS_KEY,
    STATUS_CHANNEL,
)
from fakes import FakeController, FakeFileExecutor, FakeSessionManager
from gateway.application.status_publisher import STATUS_INTERVAL, StatusPublisher

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_publisher(
    *,
    running: bool = False,
    active_session: dict | None = None,
    status_report: dict | None = None,
    parser_state: dict | None = None,
) -> tuple[StatusPublisher, FakeController, FakeFileExecutor, FakeSessionManager, MagicMock]:
    controller = FakeController(
        status_report=status_report or {"state": "Idle"},
        parser_state=parser_state or {"modal": {}},
    )
    session_manager = FakeSessionManager(active_session=active_session)
    file_executor = FakeFileExecutor(running=running)
    redis_mock = MagicMock()
    publisher = StatusPublisher(
        controller,
        session_manager,
        file_executor,
        redis_conn=redis_mock,
    )
    return publisher, controller, file_executor, session_manager, redis_mock


# ---------------------------------------------------------------------------
# gateway_state property
# ---------------------------------------------------------------------------


class TestGatewayStateProp:
    def test_default_value_is_idle(self):
        publisher, *_, _ = make_publisher()
        assert publisher.gateway_state == GW_STATE_IDLE

    def test_setter_persists_to_redis(self):
        publisher, *_, redis_mock = make_publisher()
        publisher.gateway_state = GW_STATE_STREAMING
        redis_mock.set.assert_called_with(GATEWAY_STATE_KEY, GW_STATE_STREAMING)


# ---------------------------------------------------------------------------
# publish_if_due
# ---------------------------------------------------------------------------


class TestPublishIfDue:
    def test_not_publishes_before_interval(self):
        publisher, *_, redis_mock = make_publisher()
        with patch("gateway.application.status_publisher.time") as mock_time:
            mock_time.time.side_effect = [0.0, 0.05]  # elapsed < STATUS_INTERVAL
            publisher.publish_if_due()  # sets _last_publish = 0.0
            result = publisher.publish_if_due()
        assert result is False
        redis_mock.publish.assert_not_called()

    def test_publishes_when_interval_elapsed(self):
        publisher, *_, redis_mock = make_publisher()
        with patch("gateway.application.status_publisher.time") as mock_time:
            mock_time.time.side_effect = [0.0, STATUS_INTERVAL + 0.01]
            publisher.publish_if_due()
            result = publisher.publish_if_due()
        assert result is True
        redis_mock.publish.assert_called()


# ---------------------------------------------------------------------------
# publish_now
# ---------------------------------------------------------------------------


class TestPublishNow:
    def test_publishes_immediately(self):
        publisher, *_, redis_mock = make_publisher()
        publisher.publish_now()
        redis_mock.publish.assert_called_once()
        channel = redis_mock.publish.call_args.args[0]
        assert channel == STATUS_CHANNEL

    def test_persists_snapshot(self):
        publisher, *_, redis_mock = make_publisher()
        publisher.publish_now()
        # redis.set is called for LAST_STATUS_KEY
        set_keys = [call.args[0] for call in redis_mock.set.call_args_list]
        assert LAST_STATUS_KEY in set_keys


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------


class TestCleanup:
    def test_deletes_keys(self):
        """Test that cleanup removes the gateway state and last status keys from Redis."""
        publisher, *_, redis_mock = make_publisher()
        publisher.cleanup()
        deleted_keys = [call.args[0] for call in redis_mock.delete.call_args_list]
        assert GATEWAY_STATE_KEY in deleted_keys
        assert LAST_STATUS_KEY in deleted_keys


# ---------------------------------------------------------------------------
# publish payload structure
# ---------------------------------------------------------------------------


class TestPublishStatusPayload:
    def _get_published_payload(self, redis_mock: MagicMock) -> dict:
        raw = redis_mock.publish.call_args.args[1]
        return json.loads(raw)

    def test_payload_has_required_keys(self):
        publisher, *_, redis_mock = make_publisher()
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert "status" in payload
        assert "parserstate" in payload
        assert "gateway_state" in payload
        assert "session" in payload
        assert "file_progress" in payload

    def test_payload_status_comes_from_controller(self):
        publisher, *_, redis_mock = make_publisher(status_report={"state": "Run"})
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["status"] == {"state": "Run"}

    def test_payload_parserstate_comes_from_controller(self):
        publisher, *_, redis_mock = make_publisher(parser_state={"modal": {"motion": "G0"}})
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["parserstate"] == {"modal": {"motion": "G0"}}

    def test_file_progress_is_none_when_not_running(self):
        publisher, *_, redis_mock = make_publisher(running=False)
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["file_progress"] is None

    def test_file_progress_populated_when_running(self):
        publisher, _, file_executor, _, redis_mock = make_publisher(running=True)
        file_executor.get_progress.return_value = {"sent_lines": 5, "total_lines": 10}
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["file_progress"] == {"sent_lines": 5, "total_lines": 10}

    def test_session_comes_from_session_manager(self):
        session = {"session_id": "abc", "user_id": 1}
        publisher, *_, redis_mock = make_publisher(active_session=session)
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["session"] == session

    def test_session_is_none_without_active_session(self):
        publisher, *_, redis_mock = make_publisher(active_session=None)
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["session"] is None

    def test_gateway_state_reflects_current_state(self):
        publisher, *_, redis_mock = make_publisher()
        publisher.gateway_state = GW_STATE_STREAMING
        publisher.publish_now()
        payload = self._get_published_payload(redis_mock)
        assert payload["gateway_state"] == GW_STATE_STREAMING
