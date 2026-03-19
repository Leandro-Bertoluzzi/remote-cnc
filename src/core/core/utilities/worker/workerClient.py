"""Unified Celery client for inspecting and dispatching tasks to the worker.

Consolidates the functionality previously split between ``utils.py`` and
``scheduler.py`` into a single cohesive class.

Uses ``app.send_task()`` so the API / desktop can dispatch work to the broker
by task *name* only — no worker code is imported.
"""

from functools import reduce
from typing import Any, Optional

from celery import Celery
from celery.result import AsyncResult
from typing_extensions import TypedDict

from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Types definition
RegisteredTaskList = dict[str, list[str]]
ActiveTaskList = dict[str, list[Any]]
WorkerStatus = TypedDict(
    "WorkerStatus",
    {
        "connected": bool,
        "running": bool,
        "stats": dict,
        "registered_tasks": Optional[RegisteredTaskList],
        "active_tasks": Optional[ActiveTaskList],
    },
)


class WorkerClient:
    """High-level wrapper around the Celery broker for inspection & dispatch."""

    def __init__(self) -> None:
        self._app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def is_on(self) -> bool:
        """Return whether the worker process is running."""
        inspector = self._app.control.inspect()
        return not not inspector.ping()

    def is_running(self) -> bool:
        """Return whether the worker is currently executing a task."""
        inspector = self._app.control.inspect()
        active_tasks = inspector.active()
        if not active_tasks:
            return False
        tasks_count = reduce(lambda x, tasks: x + len(tasks), active_tasks.values(), 0)
        return tasks_count > 0

    def get_status(self) -> WorkerStatus:
        """Return a full status snapshot of the worker."""
        inspector = self._app.control.inspect()
        return {
            "connected": self.is_on(),
            "running": self.is_running(),
            "stats": inspector.stats(),
            "registered_tasks": inspector.registered(),
            "active_tasks": inspector.active(),
        }

    # ------------------------------------------------------------------
    # Task dispatchers – each returns an AsyncResult (same as .delay())
    # ------------------------------------------------------------------

    def send_task(self, db_task_id: int) -> str:
        """Dispatch *execute_task* to the worker and return the Celery task ID."""
        result = self._app.send_task("execute_task", args=[db_task_id])
        return result.id

    def create_thumbnail(self, file_id: int) -> AsyncResult:
        """Dispatch *create_thumbnail* to the worker."""
        return self._app.send_task("create_thumbnail", args=[file_id])

    def generate_file_report(self, file_id: int) -> AsyncResult:
        """Dispatch *generate_report* to the worker."""
        return self._app.send_task("generate_report", args=[file_id])
