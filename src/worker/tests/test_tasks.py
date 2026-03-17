import json
from unittest.mock import MagicMock

import pytest
from core.database.models import TaskStatus
from core.database.repositories.taskRepository import TaskRepository
from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENT_FILE_PROGRESS,
)
from core.utilities.gateway.gatewayClient import GatewayClient
from pytest_mock.plugin import MockerFixture
from worker.tasks.cnc import executeTask

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "abc123"


def _mock_infrastructure(mocker: MockerFixture) -> None:
    """Mock DB session and logger to prevent external connections."""
    mocker.patch("worker.tasks.cnc.get_task_logger", return_value=MagicMock())
    mocker.patch("worker.tasks.cnc.SessionLocal", return_value=MagicMock())


def _create_mock_task(task_id: int = 1) -> MagicMock:
    """Create a properly configured mock task."""
    mock_task = MagicMock()
    mock_task.status = TaskStatus.APPROVED.value
    mock_task.id = task_id
    mock_task.user_id = 1
    mock_task.tool_id = 1
    mock_task.file.user_id = 1
    mock_task.file.file_name = "test.gcode"
    return mock_task


def _make_pubsub_message(event: dict) -> dict:
    """Build a fake PubSub message dict as returned by ``pubsub.listen()``."""
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


def _mock_gateway(mocker: MockerFixture, pubsub_messages: list[dict]) -> MagicMock:
    """Create a mock GatewayClient wired into ``worker.tasks.cnc``."""
    mock_pubsub = MagicMock()
    mock_pubsub.listen.return_value = iter(pubsub_messages)

    mock_gw = MagicMock(spec=GatewayClient)
    mock_gw.is_gateway_running.return_value = True
    mock_gw.acquire_session.return_value = SESSION_ID
    mock_gw.subscribe_events.return_value = mock_pubsub
    mock_gw.release_session.return_value = True

    mocker.patch("worker.tasks.cnc.GatewayClient", return_value=mock_gw)
    return mock_gw


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_execute_task_success(mocker: MockerFixture):
    """Happy path: file finishes successfully via Gateway events."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=2)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mock_get_task = mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mock_update_status = mocker.patch.object(TaskRepository, "update_task_status")
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    pubsub_msgs = [
        _pubsub_progress(task_id=2, sent=3, processed=2, total=10),
        _pubsub_progress(task_id=2, sent=7, processed=6, total=10),
        _pubsub_finished(task_id=2, sent=10, total=10),
    ]
    mock_gw = _mock_gateway(mocker, pubsub_msgs)

    executeTask(task_id=2)

    # Assertions
    assert mock_get_task.call_count == 1
    mock_gw.acquire_session.assert_called_once_with(user_id=1, client_type="worker")
    mock_gw.request_file_execution.assert_called_once()
    mock_gw.release_session.assert_called_once_with(SESSION_ID)
    assert mock_update_status.call_count == 2  # IN_PROGRESS + FINISHED


def test_no_task_in_db(mocker: MockerFixture):
    """Task ID not found in the database."""
    _mock_infrastructure(mocker)

    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=None)
    mock_update_status = mocker.patch.object(TaskRepository, "update_task_status")
    mock_gw = _mock_gateway(mocker, [])

    with pytest.raises(Exception) as error:
        executeTask(task_id=1)

    assert str(error.value) == "No se encontró la tarea en la base de datos"
    assert mock_update_status.call_count == 0
    mock_gw.acquire_session.assert_not_called()


def test_task_in_progress_exception(mocker: MockerFixture):
    """Another task is already running."""
    _mock_infrastructure(mocker)

    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=True)
    mock_gw = _mock_gateway(mocker, [])

    with pytest.raises(Exception) as error:
        executeTask(task_id=1)

    assert str(error.value) == "Ya hay una tarea en progreso, por favor espere a que termine"
    mock_gw.acquire_session.assert_not_called()


def test_task_missing_arguments():
    """Calling without required task_id argument."""
    with pytest.raises(Exception) as error:
        executeTask()
    assert "task_id" in str(error.value)


def test_gateway_not_running(mocker: MockerFixture):
    """Gateway is offline when the task tries to start."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    mock_gw = _mock_gateway(mocker, [])
    mock_gw.is_gateway_running.return_value = False

    with pytest.raises(Exception) as error:
        executeTask(task_id=1)

    assert "Gateway no está disponible" in str(error.value)


def test_session_acquisition_fails(mocker: MockerFixture):
    """Gateway is running but session is already held by another client."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    mock_gw = _mock_gateway(mocker, [])
    mock_gw.acquire_session.return_value = None

    with pytest.raises(Exception) as error:
        executeTask(task_id=1)

    assert "No se pudo adquirir la sesión" in str(error.value)


def test_file_execution_failed_event(mocker: MockerFixture):
    """Gateway reports file_failed → task marked FAILED."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mock_update_status = mocker.patch.object(TaskRepository, "update_task_status")
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    pubsub_msgs = [_pubsub_failed(task_id=1, error="GRBL alarm")]
    mock_gw = _mock_gateway(mocker, pubsub_msgs)

    with pytest.raises(Exception, match="GRBL alarm"):
        executeTask(task_id=1)

    # IN_PROGRESS then FAILED
    assert mock_update_status.call_count == 2
    mock_gw.release_session.assert_called_once_with(SESSION_ID)


def test_events_for_other_task_ignored(mocker: MockerFixture):
    """Events for a different task_id are silently skipped."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=5)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mock_update_status = mocker.patch.object(TaskRepository, "update_task_status")
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    pubsub_msgs = [
        _pubsub_progress(task_id=99, sent=1, processed=1, total=10),  # ignored
        _pubsub_finished(task_id=5, sent=10, total=10),  # ours
    ]
    _mock_gateway(mocker, pubsub_msgs)

    executeTask(task_id=5)

    # Progress for task 99 was ignored, finished for task 5 was processed
    assert mock_update_status.call_count == 2  # IN_PROGRESS + FINISHED


def test_session_released_on_error(mocker: MockerFixture):
    """Session is released even when an unexpected error occurs."""
    _mock_infrastructure(mocker)

    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mocker.patch.object(TaskRepository, "update_task_status")
    mocker.patch("worker.tasks.cnc.FileSystemHelper")

    mock_gw = _mock_gateway(mocker, [])
    mock_gw.request_file_execution.side_effect = RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        executeTask(task_id=1)

    mock_gw.release_session.assert_called_once_with(SESSION_ID)
