"""Port definition for the Worker client."""

from typing import Protocol, runtime_checkable

from core.domain.worker import WorkerStatus

# ---------------------------------------------------------------------------
# Port (Protocol)
# ---------------------------------------------------------------------------


@runtime_checkable
class IWorkerClient(Protocol):
    """Minimal interface expected by all consumers of the worker subsystem."""

    def is_on(self) -> bool:
        """Return whether the worker process is reachable."""
        ...

    def is_running(self) -> bool:
        """Return whether the worker is currently executing a task."""
        ...

    def get_status(self) -> WorkerStatus:
        """Return a full status snapshot of the worker."""
        ...

    def send_task(self, db_task_id: int) -> str:
        """Dispatch *execute_task* to the worker and return the task ID."""
        ...

    def create_thumbnail(self, file_id: int) -> str:
        """Dispatch *create_thumbnail* to the worker and return the task ID."""
        ...

    def generate_file_report(self, file_id: int) -> str:
        """Dispatch *generate_report* to the worker and return the task ID."""
        ...
