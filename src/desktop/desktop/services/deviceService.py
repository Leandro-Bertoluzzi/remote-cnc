"""Service layer for Device/Worker operations (Celery + Redis + Gateway)."""

import logging

import core.utilities.worker.utils as worker
from core.utilities.gateway.constants import ACTION_PAUSE, ACTION_RESUME
from core.utilities.gateway.gatewayClient import GatewayClient
from core.utilities.worker.workerStatusManager import WorkerStoreAdapter

logger = logging.getLogger(__name__)

# Module-level shared GatewayClient instance
_gateway_client: GatewayClient | None = None


def _get_gateway() -> GatewayClient:
    global _gateway_client  # noqa: PLW0603
    if _gateway_client is None:
        _gateway_client = GatewayClient()
    return _gateway_client


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
    def set_device_enabled(cls, enabled: bool) -> None:
        WorkerStoreAdapter.set_device_enabled(enabled)

    # --- Gateway pause/resume ---

    @classmethod
    def request_pause(cls) -> None:
        """Send a pause realtime command to the Gateway using the active session."""
        gw = _get_gateway()
        session = gw.get_active_session()
        if session is None:
            raise RuntimeError("No hay sesión activa para pausar")
        gw.send_realtime(session["session_id"], ACTION_PAUSE)

    @classmethod
    def request_resume(cls) -> None:
        """Send a resume realtime command to the Gateway using the active session."""
        gw = _get_gateway()
        session = gw.get_active_session()
        if session is None:
            raise RuntimeError("No hay sesión activa para retomar")
        gw.send_realtime(session["session_id"], ACTION_RESUME)

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
