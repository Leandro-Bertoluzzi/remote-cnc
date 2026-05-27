"""Tests for the CNC execution handler."""

import json
from unittest.mock import MagicMock

import pytest
from core.domain.gateway import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENT_FILE_PROGRESS,
)
from core.domain.task import TaskStatus
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.task_repository import ITaskRepository
from worker.tasks.handlers.cnc_handler import execute_cnc_task

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "abc123"


def _make_task(task_id: int = 1) -> MagicMock:
    task = MagicMock()
    task.status = TaskStatus.APPROVED.value
    task.id = task_id
    task.user_id = 1
    task.file.user_id = 1
    task.file.file_name = "test.gcode"
    return task


def _make_pubsub_message(event: dict) -> dict:
    return {"type": "message", "data": json.dumps(event)}


def _pubsub_finished(task_id: int, sent: int = 10, total: int = 10) -> dict:
    return _make_pubsub_message(
        {"type": EVENT_FILE_FINISHED, "task_id": task_id, "sent_lines": sent, "total_lines": total}
    )


def _pubsub_failed(task_id: int, error: str = "Error desconocido") -> dict:
    return _make_pubsub_message({"type": EVENT_FILE_FAILED, "task_id": task_id, "error": error})


def _pubsub_progress(task_id: int, sent: int = 5, processed: int = 4, total: int = 10) -> dict:
    return _make_pubsub_message(
        {
            "type": EVENT_FILE_PROGRESS,
            "task_id": task_id,
            "sent_lines": sent,
            "processed_lines": processed,
            "total_lines": total,
        }
    )


def _make_gateway(pubsub_messages: list) -> MagicMock:
    mock_pubsub = MagicMock()
    mock_pubsub.listen.return_value = iter(pubsub_messages)

    mock_gw = MagicMock(spec=IGatewayClient)
    mock_gw.is_gateway_running.return_value = True
    mock_gw.acquire_session.return_value = SESSION_ID
    mock_gw.subscribe_events.return_value = mock_pubsub
    mock_gw.release_session.return_value = True
    return mock_gw


def _call(task_id: int, repo: MagicMock, gateway: MagicMock, storage: MagicMock | None = None):
    if storage is None:
        storage = MagicMock(spec=IFileStorage)
    execute_cnc_task(
        task_id=task_id,
        repo=repo,
        storage=storage,
        gateway=gateway,
        task_logger=MagicMock(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_execute_task_success():
    """Happy path: file finishes successfully via Gateway events."""
    task = _make_task(task_id=2)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway(
        [
            _pubsub_progress(task_id=2, sent=3, processed=2, total=10),
            _pubsub_progress(task_id=2, sent=7, processed=6, total=10),
            _pubsub_finished(task_id=2, sent=10, total=10),
        ]
    )

    _call(task_id=2, repo=repo, gateway=gw)

    repo.get_task_by_id.assert_called_once_with(2)
    gw.acquire_session.assert_called_once_with(user_id=1, client_type="worker")
    gw.request_file_execution.assert_called_once()
    gw.release_session.assert_called_once_with(SESSION_ID)
    assert repo.update_task_status.call_count == 2  # IN_PROGRESS + FINISHED


def test_no_task_in_db():
    """Task ID not found in the database."""
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = None

    gw = _make_gateway([])

    with pytest.raises(Exception, match="No se encontró la tarea en la base de datos"):
        _call(task_id=1, repo=repo, gateway=gw)

    repo.update_task_status.assert_not_called()
    gw.acquire_session.assert_not_called()


def test_task_in_progress_exception():
    """Another task is already running."""
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = True

    gw = _make_gateway([])

    with pytest.raises(Exception, match="Ya hay una tarea en progreso"):
        _call(task_id=1, repo=repo, gateway=gw)

    gw.acquire_session.assert_not_called()


def test_gateway_not_running():
    """Gateway is offline when the task tries to start."""
    task = _make_task(task_id=1)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway([])
    gw.is_gateway_running.return_value = False

    with pytest.raises(Exception, match="Gateway no está disponible"):
        _call(task_id=1, repo=repo, gateway=gw)


def test_session_acquisition_fails():
    """Gateway is running but session is already held by another client."""
    task = _make_task(task_id=1)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway([])
    gw.acquire_session.return_value = None

    with pytest.raises(Exception, match="No se pudo adquirir la sesión"):
        _call(task_id=1, repo=repo, gateway=gw)


def test_file_execution_failed_event():
    """Gateway reports file_failed → task marked FAILED."""
    task = _make_task(task_id=1)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway([_pubsub_failed(task_id=1, error="GRBL alarm")])

    with pytest.raises(Exception, match="GRBL alarm"):
        _call(task_id=1, repo=repo, gateway=gw)

    # IN_PROGRESS then FAILED
    assert repo.update_task_status.call_count == 2
    gw.release_session.assert_called_once_with(SESSION_ID)


def test_events_for_other_task_ignored():
    """Events for a different task_id are silently skipped."""
    task = _make_task(task_id=5)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway(
        [
            _pubsub_progress(task_id=99, sent=1, processed=1, total=10),  # ignored
            _pubsub_finished(task_id=5, sent=10, total=10),  # ours
        ]
    )

    _call(task_id=5, repo=repo, gateway=gw)

    assert repo.update_task_status.call_count == 2  # IN_PROGRESS + FINISHED


def test_session_released_on_error():
    """Session is released even when an unexpected error occurs."""
    task = _make_task(task_id=1)
    repo = MagicMock(spec=ITaskRepository)
    repo.are_there_tasks_in_progress.return_value = False
    repo.get_task_by_id.return_value = task

    gw = _make_gateway([])
    gw.request_file_execution.side_effect = RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        _call(task_id=1, repo=repo, gateway=gw)

    gw.release_session.assert_called_once_with(SESSION_ID)
