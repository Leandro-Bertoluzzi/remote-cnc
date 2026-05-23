"""Port for task persistence operations."""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from core.domain.entities import Task
from core.domain.task import TASK_EMPTY_NOTE


@runtime_checkable
class ITaskRepository(Protocol):
    def create_task(
        self,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = TASK_EMPTY_NOTE,
    ) -> Task: ...

    def get_task_by_id(self, id: int) -> Task | None: ...

    def get_all_tasks_from_user(self, user_id: int, status: str = "all") -> list[Task]: ...

    def get_all_tasks(self, status: str = "all") -> list[Task]: ...

    def are_there_tasks_with_status(self, status: str) -> bool: ...

    def are_there_pending_tasks(self) -> bool: ...

    def are_there_tasks_in_progress(self) -> bool: ...

    def update_task(
        self,
        id: int,
        user_id: int,
        file_id: Optional[int] = None,
        tool_id: Optional[int] = None,
        material_id: Optional[int] = None,
        name: Optional[str] = None,
        note: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Task: ...

    def update_task_status(
        self,
        id: int,
        status: str,
        admin_id: Optional[int] = None,
        cancellation_reason: str = "",
    ) -> Task: ...

    def remove_task(self, id: int) -> None: ...
