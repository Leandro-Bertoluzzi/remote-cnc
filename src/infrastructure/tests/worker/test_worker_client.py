"""Unit tests for WorkerClient.

The broker is replaced with a MagicMock so no Celery connection is needed.
"""

from unittest.mock import MagicMock

import pytest
from infrastructure.worker.broker import ITaskBroker
from infrastructure.worker.worker_client import (
    _TASK_EXECUTE,
    _TASK_REPORT,
    _TASK_THUMBNAIL,
    WorkerClient,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_result():
    """A minimal task-result stub with a predictable id."""
    result = MagicMock()
    result.id = "task-abc"
    return result


@pytest.fixture()
def mock_broker(mock_result):
    """An ITaskBroker mock with sensible defaults."""
    broker = MagicMock(spec=ITaskBroker)
    broker.ping.return_value = {"worker@host": {"ok": "pong"}}
    broker.get_active_tasks.return_value = {"worker@host": []}
    broker.get_stats.return_value = {"worker@host": {"pid": 1234, "uptime": 60}}
    broker.get_registered_tasks.return_value = {"worker@host": ["execute_task"]}
    broker.dispatch.return_value = mock_result
    return broker


@pytest.fixture()
def client(mock_broker) -> WorkerClient:
    return WorkerClient(broker=mock_broker)


# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


class TestWorkerClientInspection:
    def test_is_on_returns_true_when_broker_pings(self, client, mock_broker):
        mock_broker.ping.return_value = {"worker@host": {"ok": "pong"}}
        assert client.is_on() is True

    def test_is_on_returns_false_when_broker_returns_none(self, client, mock_broker):
        mock_broker.ping.return_value = None
        assert client.is_on() is False

    def test_is_on_returns_false_when_broker_returns_empty(self, client, mock_broker):
        mock_broker.ping.return_value = {}
        assert client.is_on() is False

    def test_is_running_true_when_active_tasks_present(self, client, mock_broker):
        mock_broker.get_active_tasks.return_value = {"worker@host": ["t1", "t2"]}
        assert client.is_running() is True

    def test_is_running_false_when_no_active_tasks(self, client, mock_broker):
        mock_broker.get_active_tasks.return_value = {"worker@host": []}
        assert client.is_running() is False

    def test_is_running_false_when_broker_returns_none(self, client, mock_broker):
        mock_broker.get_active_tasks.return_value = None
        assert client.is_running() is False

    def test_get_status_has_expected_keys(self, client):
        status = client.get_status()
        assert set(status.keys()) == {
            "connected",
            "running",
            "stats",
            "registered_tasks",
            "active_tasks",
        }

    def test_get_status_connected_reflects_is_on(self, client, mock_broker):
        mock_broker.ping.return_value = {"worker@host": {"ok": "pong"}}
        assert client.get_status()["connected"] is True

        mock_broker.ping.return_value = None
        assert client.get_status()["connected"] is False

    def test_get_status_running_reflects_is_running(self, client, mock_broker):
        mock_broker.get_active_tasks.return_value = {"worker@host": ["t1"]}
        assert client.get_status()["running"] is True

        mock_broker.get_active_tasks.return_value = {"worker@host": []}
        assert client.get_status()["running"] is False


# ---------------------------------------------------------------------------
# Dispatchers
# ---------------------------------------------------------------------------


class TestWorkerClientDispatchers:
    def test_send_task_dispatches_correct_name_and_returns_id(self, client, mock_broker):
        result = client.send_task(42)
        mock_broker.dispatch.assert_called_once_with(_TASK_EXECUTE, [42])
        assert result == "task-abc"

    def test_create_thumbnail_dispatches_correct_name_and_returns_id(self, client, mock_broker):
        result = client.create_thumbnail(7)
        mock_broker.dispatch.assert_called_once_with(_TASK_THUMBNAIL, [7])
        assert result == "task-abc"

    def test_generate_file_report_dispatches_correct_name_and_returns_id(self, client, mock_broker):
        result = client.generate_file_report(3)
        mock_broker.dispatch.assert_called_once_with(_TASK_REPORT, [3])
        assert result == "task-abc"
