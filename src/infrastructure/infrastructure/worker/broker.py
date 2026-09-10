"""Internal abstraction for the task broker."""

from typing import Optional, Protocol, runtime_checkable

from core.domain.worker import (
    ActiveTasksResponse,
    PingResponse,
    RegisteredTasksResponse,
    StatsResponse,
)


@runtime_checkable
class ITaskResult(Protocol):
    """Minimal interface for a dispatched-task handle."""

    id: str


@runtime_checkable
class ITaskBroker(Protocol):
    """Low-level task-dispatch interface over a message broker."""

    def ping(self) -> Optional[PingResponse]:
        """Ping all workers and return a mapping of {worker: pong}."""
        ...

    def get_active_tasks(self) -> Optional[ActiveTasksResponse]:
        """Return currently executing tasks for each worker."""
        ...

    def get_stats(self) -> Optional[StatsResponse]:
        """Return worker statistics."""
        ...

    def get_registered_tasks(self) -> Optional[RegisteredTasksResponse]:
        """Return tasks registered in each worker."""
        ...

    def dispatch(self, task_name: str, args: list) -> ITaskResult:
        """Send *task_name* with *args* to the broker and return the result handle."""
        ...
