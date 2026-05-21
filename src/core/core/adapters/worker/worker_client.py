"""Concrete implementation of ``IWorkerClient``."""

from functools import reduce

from core.adapters.worker.broker import ITaskBroker
from core.adapters.worker.celery_broker import CeleryTaskBroker
from core.domain.worker import WorkerStatus

# ------------------------------------------------------------------
# Task-name constants (adapter-internal — not part of the domain)
# ------------------------------------------------------------------
_TASK_EXECUTE = "execute_task"
_TASK_THUMBNAIL = "create_thumbnail"
_TASK_REPORT = "generate_report"


class WorkerClient:
    """High-level wrapper around the broker for inspection and dispatch."""

    def __init__(self, broker: ITaskBroker) -> None:
        self._broker = broker

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls) -> "WorkerClient":
        """Create a ``WorkerClient`` backed by a Celery broker from ``core.config``."""
        return cls(broker=CeleryTaskBroker.from_config())

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def is_on(self) -> bool:
        """Return whether the worker process is running."""
        return not not self._broker.ping()

    def is_running(self) -> bool:
        """Return whether the worker is currently executing a task."""
        active_tasks = self._broker.get_active_tasks()
        if not active_tasks:
            return False
        tasks_count = reduce(lambda x, tasks: x + len(tasks), active_tasks.values(), 0)
        return tasks_count > 0

    def get_status(self) -> WorkerStatus:
        """Return a full status snapshot of the worker."""
        return {
            "connected": self.is_on(),
            "running": self.is_running(),
            "stats": self._broker.get_stats(),
            "registered_tasks": self._broker.get_registered_tasks(),
            "active_tasks": self._broker.get_active_tasks(),
        }

    # ------------------------------------------------------------------
    # Task dispatchers
    # ------------------------------------------------------------------

    def send_task(self, db_task_id: int) -> str:
        """Dispatch *execute_task* to the worker and return the task ID."""
        return self._broker.dispatch(_TASK_EXECUTE, [db_task_id]).id

    def create_thumbnail(self, file_id: int) -> str:
        """Dispatch *create_thumbnail* to the worker and return the task ID."""
        return self._broker.dispatch(_TASK_THUMBNAIL, [file_id]).id

    def generate_file_report(self, file_id: int) -> str:
        """Dispatch *generate_report* to the worker and return the task ID."""
        return self._broker.dispatch(_TASK_REPORT, [file_id]).id
