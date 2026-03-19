from unittest.mock import MagicMock

from core.database.models import Task
from desktop.services.taskService import TaskService
from pytest_mock.plugin import MockerFixture


class TestTaskService:
    """Tests for TaskService methods with meaningful logic."""

    # --- create_and_execute_task ---

    def test_create_and_execute_task(self, mocker: MockerFixture):
        mock_task = MagicMock(spec=Task)
        mock_task.id = 42

        mocker.patch("desktop.services.taskService.get_db_session")
        mock_repo_class = mocker.patch("desktop.services.taskService.TaskRepository")
        mock_repo = mock_repo_class.return_value
        mock_repo.create_task.return_value = mock_task
        mock_client = mocker.patch("desktop.services.taskService.WorkerClient")
        mock_client_instance = mock_client.return_value
        mock_client_instance.send_task.return_value = "worker-id"

        result = TaskService.create_and_execute_task(1, 2, 3, 4, "test task", "note")

        assert result == "worker-id"
        mock_repo.create_task.assert_called_once_with(1, 2, 3, 4, "test task", "note")
        mock_client_instance.send_task.assert_called_once_with(42)
