"""Service layer for Device/Worker operations (Celery + Redis)."""

import logging

import core.utilities.worker.utils as worker
from celery.result import AsyncResult
from core.utilities.worker.workerStatusManager import WorkerStoreAdapter

logger = logging.getLogger(__name__)


class DeviceService:
    """Encapsulates all worker/device status operations (Celery inspect + Redis)."""

    # --- Worker/Celery status ---

    @classmethod
    def is_worker_connected(cls) -> bool:
        """Whether the Celery worker process is reachable."""
        return worker.is_worker_on()

    @classmethod
    def is_worker_busy(cls) -> bool:
        """Whether the Celery worker is currently executing a task."""
        return worker.is_worker_running()

    # --- Device status (Redis store) ---

    @classmethod
    def is_device_enabled(cls) -> bool:
        return WorkerStoreAdapter.is_device_enabled()

    @classmethod
    def is_device_paused(cls) -> bool:
        return WorkerStoreAdapter.is_device_paused()

    @classmethod
    def set_device_enabled(cls, enabled: bool) -> None:
        WorkerStoreAdapter.set_device_enabled(enabled)

    @classmethod
    def request_pause(cls) -> None:
        WorkerStoreAdapter.request_pause()

    @classmethod
    def request_resume(cls) -> None:
        WorkerStoreAdapter.request_resume()

    # --- Combined checks ---

    @classmethod
    def is_device_available(cls) -> bool:
        """Whether the device is ready to accept a new task.

        This combines: worker connected + device enabled + not busy.
        """
        return cls.is_worker_connected() and cls.is_device_enabled() and not cls.is_worker_busy()

    @classmethod
    def check_device_availability(cls) -> str | None:
        """Check if device is available for executing a task.

        Returns ``None`` if available, or a user-facing error message
        (in Spanish) describing why it is not.
        """
        if not cls.is_worker_connected():
            return "Ejecución cancelada: El worker no está conectado"

        if not cls.is_device_enabled():
            return "Ejecución cancelada: El equipo está deshabilitado"

        if cls.is_worker_busy():
            return "Ejecución cancelada: Ya hay una tarea en progreso"

        return None

    # --- Celery task monitoring ---

    @classmethod
    def get_celery_task_status(cls, worker_task_id: str) -> dict:
        """Query the Celery result backend for the status of a task.

        Returns ``{"status": str, "info": Any}``.
        """
        task_state: AsyncResult = AsyncResult(worker_task_id)
        return {"status": task_state.status, "info": task_state.info}
