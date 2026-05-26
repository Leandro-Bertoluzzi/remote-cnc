"""Service layer for Worker and Gateway operations."""

import logging

from core.domain.gateway import ACTION_PAUSE, ACTION_RESUME
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient

logger = logging.getLogger(__name__)

# Module-level port references — set once by configure() at startup.
# Services never instantiate concrete adapters directly.
_gateway: IGatewayClient | None = None
_worker: IWorkerClient | None = None


def configure(gateway: IGatewayClient, worker: IWorkerClient) -> None:
    """Inject the port implementations used by ``DeviceService``.

    Must be called from the composition root (``desktop/main.py``)
    before any ``DeviceService`` method is invoked.
    """
    global _gateway, _worker  # noqa: PLW0603
    _gateway = gateway
    _worker = worker


def _get_gateway() -> IGatewayClient:
    if _gateway is None:
        raise RuntimeError(
            "DeviceService has not been configured. "
            "Call desktop.services.deviceService.configure() first."
        )
    return _gateway


def _get_worker() -> IWorkerClient:
    if _worker is None:
        raise RuntimeError(
            "DeviceService has not been configured. "
            "Call desktop.services.deviceService.configure() first."
        )
    return _worker


class DeviceService:
    """Encapsulates all worker and gateway status operations."""

    # --- Worker status ---

    @classmethod
    def is_worker_connected(cls) -> bool:
        """Whether the worker process is reachable."""
        return _get_worker().is_on()

    @classmethod
    def is_worker_busy(cls) -> bool:
        """Whether the worker is currently executing a task."""
        return _get_worker().is_running()

    # --- Gateway status ---

    @classmethod
    def is_gateway_running(cls) -> bool:
        """Whether the CNC Gateway process is running."""
        return _get_gateway().is_gateway_running()

    @classmethod
    def has_active_session(cls) -> bool:
        """Whether there is an active CNC session."""
        return _get_gateway().get_active_session() is not None

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

        This combines: worker connected + gateway running + no active session.
        """
        return (
            cls.is_worker_connected()
            and cls.is_gateway_running()
            and not cls.has_active_session()
            and not cls.is_worker_busy()
        )

    @classmethod
    def check_device_availability(cls) -> str | None:
        """Check if device is available for executing a task.

        Returns ``None`` if available, or a user-facing error message
        (in Spanish) describing why it is not.
        """
        if not cls.is_worker_connected():
            return "Ejecución cancelada: El worker no está conectado"

        if not cls.is_gateway_running():
            return "Ejecución cancelada: El Gateway CNC no está disponible"

        if cls.has_active_session():
            return "Ejecución cancelada: El CNC está en uso por otra sesión"

        if cls.is_worker_busy():
            return "Ejecución cancelada: Ya hay una tarea en progreso"

        return None
