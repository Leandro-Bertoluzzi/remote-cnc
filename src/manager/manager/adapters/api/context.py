"""Application context for the FastAPI application."""

from __future__ import annotations

from dataclasses import dataclass

from core.ports.db_session import SessionFactory
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.logger import ILogger
from core.ports.worker_client import IWorkerClient
from manager.application.device_service import DeviceService
from manager.application.file_service import FileService
from manager.application.log_service import LogService
from manager.application.material_service import MaterialService
from manager.application.task_service import TaskService
from manager.application.tool_service import ToolService
from manager.application.user_service import UserService


@dataclass
class AppContext:
    """Container for API infrastructure and application services."""

    gateway: IGatewayClient
    worker: IWorkerClient
    file_storage: IFileStorage
    session_factory: SessionFactory
    logger: ILogger
    device_service: DeviceService
    file_service: FileService
    log_service: LogService
    material_service: MaterialService
    task_service: TaskService
    tool_service: ToolService
    user_service: UserService
