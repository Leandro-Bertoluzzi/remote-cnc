from unittest.mock import MagicMock

from core.domain.entities import Task
from core.domain.task import TaskStatus
from desktop.services.taskService import TaskService
from pytest_mock.plugin import MockerFixture


class TestTaskService:
    @staticmethod
    def _mock_db_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.taskService.get_db_session", return_value=session_ctx)
        repository = MagicMock()
        get_repo = mocker.patch(
            "desktop.services.taskService.get_task_repository",
            return_value=repository,
        )
        return session, repository, get_repo

    def test_get_all_tasks(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected_tasks = [MagicMock(spec=Task), MagicMock(spec=Task)]
        repository.get_all_tasks_from_user.return_value = expected_tasks

        result = TaskService.get_all_tasks(user_id=7, status="on_hold")

        assert result == expected_tasks
        get_repo.assert_called_once_with(session)
        repository.get_all_tasks_from_user.assert_called_once_with(7, status="on_hold")

    def test_create_task(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected_task = MagicMock(spec=Task)
        repository.create_task.return_value = expected_task

        result = TaskService.create_task(1, 2, 3, 4, "Tarea", "Nota")

        assert result == expected_task
        get_repo.assert_called_once_with(session)
        repository.create_task.assert_called_once_with(1, 2, 3, 4, "Tarea", "Nota")

    def test_update_task_status(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        TaskService.update_task_status(
            task_id=10,
            new_status=TaskStatus.CANCELLED.value,
            admin_id=99,
            cancellation_reason="cancelada",
        )

        get_repo.assert_called_once_with(session)
        repository.update_task_status.assert_called_once_with(
            10, TaskStatus.CANCELLED.value, 99, "cancelada"
        )

    def test_send_task_to_worker(self, mocker: MockerFixture):
        worker = MagicMock()
        worker.send_task.return_value = "worker-task-42"
        mocker.patch("desktop.services.taskService._get_worker_client", return_value=worker)

        result = TaskService.send_task_to_worker(42)

        assert result == "worker-task-42"
        worker.send_task.assert_called_once_with(42)

    def test_create_and_execute_task(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        created_task = MagicMock(spec=Task)
        created_task.id = 42
        repository.create_task.return_value = created_task

        worker = MagicMock()
        worker.send_task.return_value = "worker-42"
        mocker.patch("desktop.services.taskService._get_worker_client", return_value=worker)

        result = TaskService.create_and_execute_task(1, 2, 3, 4, "Auto", "run")

        assert result == "worker-42"
        get_repo.assert_called_once_with(session)
        repository.create_task.assert_called_once_with(1, 2, 3, 4, "Auto", "run")
        repository.update_task_status.assert_called_once_with(42, TaskStatus.APPROVED.value, 1)
        worker.send_task.assert_called_once_with(42)
