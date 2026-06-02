"""Tests for gateway.SessionManager."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from core.domain.gateway import (
    EVENT_SESSION_ACQUIRED,
    EVENT_SESSION_RELEASED,
    EVENTS_CHANNEL,
    SESSION_KEY,
)
from gateway.application.session_manager import SessionManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_manager(
    stored_session: dict | None = None,
) -> tuple[SessionManager, MagicMock, MagicMock]:
    """Return a (SessionManager, pubsub_mock, store_mock) tuple.

    If *stored_session* is provided it is returned by ``store.get(SESSION_KEY)``.
    """
    pubsub_mock = MagicMock()
    store_mock = MagicMock()
    store_mock.get.return_value = json.dumps(stored_session) if stored_session else None
    store_mock.exists.return_value = 1 if stored_session else 0
    manager = SessionManager(pubsub_client=pubsub_mock, store=store_mock)
    return manager, pubsub_mock, store_mock


def _published_events(pubsub_mock: MagicMock) -> list[dict]:
    return [
        json.loads(call.args[1])
        for call in pubsub_mock.publish.call_args_list
        if call.args[0] == EVENTS_CHANNEL
    ]


# ---------------------------------------------------------------------------
# get_active_session
# ---------------------------------------------------------------------------


class TestGetActiveSession:
    def test_returns_none_when_no_session(self):
        manager, *_ = make_manager()
        assert manager.get_active_session() is None

    def test_returns_decoded_session(self):
        session = {"session_id": "abc123", "user_id": 1}
        manager, *_ = make_manager(stored_session=session)
        assert manager.get_active_session() == session

    def test_reads_from_session_key(self):
        manager, _, store_mock = make_manager()
        manager.get_active_session()
        store_mock.get.assert_called_with(SESSION_KEY)


# ---------------------------------------------------------------------------
# validate_session
# ---------------------------------------------------------------------------


class TestValidateSession:
    def test_returns_true_for_matching_session_id(self):
        manager, *_ = make_manager(stored_session={"session_id": "abc123"})
        assert manager.validate_session("abc123") is True

    def test_returns_false_for_wrong_session_id(self):
        manager, *_ = make_manager(stored_session={"session_id": "abc123"})
        assert manager.validate_session("wrong") is False

    def test_returns_false_when_no_active_session(self):
        manager, *_ = make_manager()
        assert manager.validate_session("abc123") is False


# ---------------------------------------------------------------------------
# has_active_session
# ---------------------------------------------------------------------------


class TestHasActiveSession:
    def test_returns_true_when_session_key_exists(self):
        manager, *_ = make_manager(stored_session={"session_id": "x"})
        assert manager.has_active_session() is True

    def test_returns_false_when_session_key_missing(self):
        manager, *_ = make_manager()
        assert manager.has_active_session() is False


# ---------------------------------------------------------------------------
# publish_session_acquired
# ---------------------------------------------------------------------------


class TestPublishSessionAcquired:
    def test_publishes_to_events_channel(self):
        manager, pubsub_mock, _ = make_manager()
        manager.publish_session_acquired({"session_id": "s1", "user_id": 7})
        pubsub_mock.publish.assert_called_once()
        channel = pubsub_mock.publish.call_args.args[0]
        assert channel == EVENTS_CHANNEL

    def test_event_contains_session_data(self):
        session_data = {"session_id": "s1", "user_id": 7, "client_type": "desktop"}
        manager, pubsub_mock, _ = make_manager()
        manager.publish_session_acquired(session_data)
        events = _published_events(pubsub_mock)
        assert len(events) == 1
        assert events[0]["type"] == EVENT_SESSION_ACQUIRED
        assert events[0]["session"] == session_data


# ---------------------------------------------------------------------------
# publish_session_released
# ---------------------------------------------------------------------------


class TestPublishSessionReleased:
    def test_publishes_to_events_channel(self):
        manager, pubsub_mock, _ = make_manager()
        manager.publish_session_released("s1")
        pubsub_mock.publish.assert_called_once()
        channel = pubsub_mock.publish.call_args.args[0]
        assert channel == EVENTS_CHANNEL

    def test_event_contains_session_id(self):
        manager, pubsub_mock, _ = make_manager()
        manager.publish_session_released("s1")
        events = _published_events(pubsub_mock)
        assert len(events) == 1
        assert events[0]["type"] == EVENT_SESSION_RELEASED
        assert events[0]["session_id"] == "s1"
