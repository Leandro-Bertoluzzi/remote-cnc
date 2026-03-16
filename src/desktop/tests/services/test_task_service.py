from unittest.mock import MagicMock

from celery.result import AsyncResult
from core.database.models import Task
from desktop.services.taskService import TaskService
from pytest_mock.plugin import MockerFixture


class TestTaskService:
    """Tests for TaskService methods with meaningful logic."""

    # --- get_task_worker_status ---

    def test_get_task_worker_status_no_worker_id(self, mocker: MockerFixture):
        mocker.patch("desktop.services.taskService.get_value_from_id", return_value="")
        result = TaskService.get_task_worker_status(1)
        assert result is None

    def test_get_task_worker_status_with_worker_id(self, mocker: MockerFixture):
        mocker.patch("desktop.services.taskService.get_value_from_id", return_value="abc-123")
        mocker.patch.object(AsyncResult, "__init__", return_value=None)
        mocker.patch.object(
            AsyncResult,
            "_get_task_meta",
            return_value={"status": "PROGRESS", "result": {"sent_lines": 10}},
        )

        result = TaskService.get_task_worker_status(1)
        assert result is not None
        assert "status" in result
        assert "info" in result

    # --- create_and_execute_task ---

    def test_create_and_execute_task(self, mocker: MockerFixture):
        mock_task = MagicMock(spec=Task)
        mock_task.id = 42

        mocker.patch("desktop.services.taskService.get_db_session")
        mock_repo_class = mocker.patch("desktop.services.taskService.TaskRepository")
        mock_repo = mock_repo_class.return_value
        mock_repo.create_task.return_value = mock_task
        mock_send = mocker.patch(
            "desktop.services.taskService.send_task_to_worker", return_value="worker-id"
        )

        result = TaskService.create_and_execute_task(1, 2, 3, 4, "test task", "note")

        assert result == "worker-id"
        mock_repo.create_task.assert_called_once_with(1, 2, 3, 4, "test task", "note")
        mock_send.assert_called_once_with(42)
