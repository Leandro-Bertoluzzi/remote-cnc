"""Service layer for Task domain operations."""

import logging
from typing import Optional

from celery.result import AsyncResult
from core.database.models import TASK_DEFAULT_PRIORITY, Task, TaskStatus
from core.database.repositories.taskRepository import TaskRepository
from core.utilities.storage import get_value_from_id
from core.utilities.worker.utils import send_task_to_worker

from desktop.services import get_db_session

logger = logging.getLogger(__name__)


class TaskService:
    """Encapsulates all task-related operations (DB + Celery/Redis)."""

    @classmethod
    def get_all_tasks(cls, user_id: int, status: str = "all") -> list[Task]:
        with get_db_session() as session:
            repository = TaskRepository(session)
            return repository.get_all_tasks_from_user(user_id, status=status)

    @classmethod
    def create_task(
        cls,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = "",
    ) -> Task:
        with get_db_session() as session:
            repository = TaskRepository(session)
            return repository.create_task(user_id, file_id, tool_id, material_id, name, note)

    @classmethod
    def update_task(
        cls,
        task_id: int,
        user_id: int,
        file_id: Optional[int] = None,
        tool_id: Optional[int] = None,
        material_id: Optional[int] = None,
        name: Optional[str] = None,
        note: Optional[str] = None,
        priority: int = TASK_DEFAULT_PRIORITY,
    ) -> None:
        with get_db_session() as session:
            repository = TaskRepository(session)
            repository.update_task(
                task_id, user_id, file_id, tool_id, material_id, name, note, priority
            )

    @classmethod
    def update_task_status(
        cls,
        task_id: int,
        new_status: str,
        admin_id: int,
        cancellation_reason: str = "",
    ) -> None:
        with get_db_session() as session:
            repository = TaskRepository(session)
            repository.update_task_status(task_id, new_status, admin_id, cancellation_reason)

    @classmethod
    def remove_task(cls, task_id: int) -> None:
        with get_db_session() as session:
            repository = TaskRepository(session)
            repository.remove_task(task_id)

    @classmethod
    def get_task_worker_status(cls, task_db_id: int) -> dict | None:
        """Query Redis + Celery for the current status of a running task.

        Returns a dict ``{"status": str, "info": Any}`` or ``None``
        if no worker task is associated.
        """
        task_worker_id = get_value_from_id("task", task_db_id)
        if not task_worker_id:
            return None

        task_state: AsyncResult = AsyncResult(task_worker_id)
        return {"status": task_state.status, "info": task_state.info}

    @classmethod
    def send_task_to_worker(cls, task_db_id: int) -> str:
        """Dispatch a task to the Celery worker.

        Returns the worker task ID (string).
        """
        return send_task_to_worker(task_db_id)

    @classmethod
    def create_and_execute_task(
        cls,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = "",
    ) -> str:
        """Create a task, approve it, and send it to the worker.

        Returns the Celery worker task ID.
        """
        with get_db_session() as session:
            repository = TaskRepository(session)
            task = repository.create_task(user_id, file_id, tool_id, material_id, name, note)
            repository.update_task_status(task.id, TaskStatus.APPROVED.value, user_id)

        return send_task_to_worker(task.id)
