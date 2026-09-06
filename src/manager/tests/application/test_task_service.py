from unittest.mock import MagicMock

from core.domain.entities import Task
from core.domain.task import TaskStatus
from manager.application.task_service import TaskService


class TestTaskService:
    @staticmethod
    def _make_service_and_repo(worker=None):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        worker_mock = worker if worker is not None else MagicMock()
        service = TaskService(
            worker=worker_mock,
            session_factory=session_factory,
            task_repo_factory=MagicMock(return_value=repository),
        )
        return service, repository, worker_mock

    def test_get_all_tasks(self):
        service, repository, _ = self._make_service_and_repo()
        expected_tasks = [MagicMock(spec=Task), MagicMock(spec=Task)]
        repository.get_all_tasks_from_user.return_value = expected_tasks

        result = service.get_all_tasks(user_id=7, status="on_hold")

        assert result == expected_tasks
        repository.get_all_tasks_from_user.assert_called_once_with(7, status="on_hold")

    def test_create_task(self):
        service, repository, _ = self._make_service_and_repo()
        expected_task = MagicMock(spec=Task)
        repository.create_task.return_value = expected_task

        result = service.create_task(1, 2, 3, 4, "Tarea", "Nota")

        assert result == expected_task
        repository.create_task.assert_called_once_with(1, 2, 3, 4, "Tarea", "Nota")

    def test_update_task_status(self):
        service, repository, _ = self._make_service_and_repo()

        service.update_task_status(
            task_id=10,
            new_status=TaskStatus.CANCELLED.value,
            admin_id=99,
            cancellation_reason="cancelada",
        )

        repository.update_task_status.assert_called_once_with(
            10, TaskStatus.CANCELLED.value, 99, "cancelada"
        )

    def test_send_task_to_worker(self):
        worker = MagicMock()
        worker.send_task.return_value = "worker-task-42"
        service, _, _ = self._make_service_and_repo(worker=worker)

        result = service.send_task_to_worker(42)

        assert result == "worker-task-42"
        worker.send_task.assert_called_once_with(42)

    def test_create_and_execute_task(self):
        worker = MagicMock()
        worker.send_task.return_value = "worker-42"
        service, repository, _ = self._make_service_and_repo(worker=worker)
        created_task = MagicMock(spec=Task)
        created_task.id = 42
        repository.create_task.return_value = created_task

        result = service.create_and_execute_task(1, 2, 3, 4, "Auto", "run")

        assert result == "worker-42"
        repository.create_task.assert_called_once_with(1, 2, 3, 4, "Auto", "run")
        repository.update_task_status.assert_called_once_with(42, TaskStatus.APPROVED.value, 1)
        worker.send_task.assert_called_once_with(42)
