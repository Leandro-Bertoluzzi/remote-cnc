"""Service layer for Task domain operations."""

import logging
from typing import Optional

from core.domain.entities import Task
from core.domain.task import TASK_DEFAULT_PRIORITY, TaskStatus
from core.ports.db_session import SessionFactory
from core.ports.worker_client import IWorkerClient

from desktop.services.dependencies import get_task_repository

logger = logging.getLogger(__name__)


class TaskService:
    """Encapsulates all task-related operations (DB + worker)."""

    def __init__(self, worker: IWorkerClient, session_factory: SessionFactory):
        self._worker = worker
        self._session_factory = session_factory

    def get_all_tasks(self, user_id: int, status: str = "all") -> list[Task]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            return repository.get_all_tasks_from_user(user_id, status=status)

    def create_task(
        self,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = "",
    ) -> Task:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            return repository.create_task(user_id, file_id, tool_id, material_id, name, note)

    def update_task(
        self,
        task_id: int,
        user_id: int,
        file_id: Optional[int] = None,
        tool_id: Optional[int] = None,
        material_id: Optional[int] = None,
        name: Optional[str] = None,
        note: Optional[str] = None,
        priority: int = TASK_DEFAULT_PRIORITY,
    ) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            repository.update_task(
                task_id, user_id, file_id, tool_id, material_id, name, note, priority
            )

    def update_task_status(
        self,
        task_id: int,
        new_status: str,
        admin_id: int,
        cancellation_reason: str = "",
    ) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            repository.update_task_status(task_id, new_status, admin_id, cancellation_reason)

    def remove_task(self, task_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            repository.remove_task(task_id)

    def send_task_to_worker(self, task_db_id: int) -> str:
        """Dispatch a task to the worker.

        Returns the worker task ID (string).
        """
        return self._worker.send_task(task_db_id)

    def create_and_execute_task(
        self,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = "",
    ) -> str:
        """Create a task, approve it, and send it to the worker.

        Returns the worker task ID.
        """
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_task_repository(session)
            task = repository.create_task(user_id, file_id, tool_id, material_id, name, note)
            repository.update_task_status(task.id, TaskStatus.APPROVED.value, user_id)

        return self._worker.send_task(task.id)
