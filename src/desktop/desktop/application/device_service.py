"""Application service for Worker and Gateway operations."""

from core.domain.gateway import ACTION_PAUSE, ACTION_RESUME
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient


class DeviceService:
    """Encapsulates all worker and gateway status operations."""

    def __init__(self, gateway: IGatewayClient, worker: IWorkerClient):
        self._gateway = gateway
        self._worker = worker

    # --- Worker status ---

    def is_worker_connected(self) -> bool:
        """Whether the worker process is reachable."""
        return self._worker.is_on()

    def is_worker_busy(self) -> bool:
        """Whether the worker is currently executing a task."""
        return self._worker.is_running()

    # --- Gateway status ---

    def is_gateway_running(self) -> bool:
        """Whether the CNC Gateway process is running."""
        return self._gateway.is_gateway_running()

    def has_active_session(self) -> bool:
        """Whether there is an active CNC session."""
        return self._gateway.get_active_session() is not None

    # --- Gateway pause/resume ---

    def request_pause(self) -> None:
        """Send a pause realtime command to the Gateway using the active session."""
        session = self._gateway.get_active_session()
        if session is None:
            raise RuntimeError("No hay sesión activa para pausar")
        self._gateway.send_realtime(session["session_id"], ACTION_PAUSE)

    def request_resume(self) -> None:
        """Send a resume realtime command to the Gateway using the active session."""
        session = self._gateway.get_active_session()
        if session is None:
            raise RuntimeError("No hay sesión activa para retomar")
        self._gateway.send_realtime(session["session_id"], ACTION_RESUME)

    # --- Combined checks ---

    def is_device_available(self) -> bool:
        """Whether the device is ready to accept a new task.

        This combines: worker connected + gateway running + no active session.
        """
        return (
            self.is_worker_connected()
            and self.is_gateway_running()
            and not self.has_active_session()
            and not self.is_worker_busy()
        )

    def check_device_availability(self) -> str | None:
        """Check if device is available for executing a task.

        Returns ``None`` if available, or a user-facing error message
        (in Spanish) describing why it is not.
        """
        if not self.is_worker_connected():
            return "Ejecución cancelada: El worker no está conectado"

        if not self.is_gateway_running():
            return "Ejecución cancelada: El Gateway CNC no está disponible"

        if self.has_active_session():
            return "Ejecución cancelada: El CNC está en uso por otra sesión"

        if self.is_worker_busy():
            return "Ejecución cancelada: Ya hay una tarea en progreso"

        return None
