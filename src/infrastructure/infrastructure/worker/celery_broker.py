"""Celery-backed implementation of ``ITaskBroker``."""

from typing import Optional, cast

from celery import Celery
from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from core.domain.worker import (
    ActiveTasksResponse,
    PingResponse,
    RegisteredTasksResponse,
    StatsResponse,
)

from infrastructure.worker.broker import ITaskResult


class CeleryTaskBroker:
    """Thin wrapper around a ``Celery`` application that satisfies ``ITaskBroker``."""

    def __init__(self, app: Celery) -> None:
        self._app = app

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls) -> "CeleryTaskBroker":
        """Create a broker configured from ``core.config``."""
        app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
        return cls(app)

    # ------------------------------------------------------------------
    # ITaskBroker implementation
    # ------------------------------------------------------------------

    def ping(self) -> Optional[PingResponse]:
        return cast(Optional[PingResponse], self._app.control.inspect().ping())

    def get_active_tasks(self) -> Optional[ActiveTasksResponse]:
        return cast(Optional[ActiveTasksResponse], self._app.control.inspect().active())

    def get_stats(self) -> Optional[StatsResponse]:
        return cast(Optional[StatsResponse], self._app.control.inspect().stats())

    def get_registered_tasks(self) -> Optional[RegisteredTasksResponse]:
        return cast(Optional[RegisteredTasksResponse], self._app.control.inspect().registered())

    def dispatch(self, task_name: str, args: list) -> ITaskResult:
        return self._app.send_task(task_name, args=args)
