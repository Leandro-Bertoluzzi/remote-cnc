"""Application context for the Desktop application.

``AppContext`` is the composition root: it holds all infrastructure dependencies
and all application-layer service instances.

Views and helpers receive ``AppContext`` (or just the ports they need)
via constructor arguments — never by importing singletons directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.adapters.database.base import SessionLocal
from core.adapters.file_storage import FileSystemStorage
from core.adapters.gateway.gateway_client import GatewayClient
from core.adapters.logging.logger_factory import setup_stream_logger
from core.adapters.worker.worker_client import WorkerClient
from core.ports.db_session import SessionFactory
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.logger import ILogger
from core.ports.worker_client import IWorkerClient

from desktop.config import FILES_FOLDER_PATH, LOGS_FOLDER_PATH
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.fileService import FileService
from desktop.services.materialService import MaterialService
from desktop.services.taskService import TaskService
from desktop.services.toolService import ToolService
from desktop.services.userService import UserService


@dataclass
class AppContext:
    """Container for shared infrastructure dependencies and application services.

    Infrastructure ports are ``typing.Protocol`` instances; services are
    instantiable classes injected here at composition time.
    Concrete adapters are only referenced in ``create_app_context`` below.
    """

    # Infrastructure ports
    gateway: IGatewayClient
    worker: IWorkerClient
    file_storage: IFileStorage
    session_factory: SessionFactory
    logger: ILogger

    # Application services
    asset_service: AssetService
    device_service: DeviceService
    file_service: FileService
    material_service: MaterialService
    task_service: TaskService
    tool_service: ToolService
    user_service: UserService


def create_app_context() -> AppContext:
    """Build the production ``AppContext`` from environment config.

    This is the **sole** place in the desktop package that imports concrete
    adapter classes. Every other module receives its dependencies through
    ``AppContext`` or a port typed as a Protocol.
    """
    gateway = GatewayClient.from_config()
    worker = WorkerClient.from_config()
    storage = FileSystemStorage(FILES_FOLDER_PATH)
    session_factory = SessionLocal
    app_logger = setup_stream_logger("desktop", logging.INFO, LOGS_FOLDER_PATH)

    return AppContext(
        gateway=gateway,
        worker=worker,
        file_storage=storage,
        session_factory=session_factory,
        logger=app_logger,
        asset_service=AssetService(session_factory),
        device_service=DeviceService(gateway, worker),
        file_service=FileService(worker, storage, session_factory, app_logger),
        material_service=MaterialService(session_factory),
        task_service=TaskService(worker, session_factory),
        tool_service=ToolService(session_factory),
        user_service=UserService(session_factory),
    )
