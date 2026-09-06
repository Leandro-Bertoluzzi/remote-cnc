"""Application context for the Desktop application.

``AppContext`` is the composition root: it holds all infrastructure dependencies
and all application-layer service instances.

Views and helpers receive ``AppContext`` (or just the ports they need)
via constructor arguments — never by importing singletons directly.
"""

from __future__ import annotations

import logging

from core.adapters.database.base import SessionLocal
from core.adapters.database.file_repository import FileRepository
from core.adapters.database.material_repository import MaterialRepository
from core.adapters.database.task_repository import TaskRepository
from core.adapters.database.tool_repository import ToolRepository
from core.adapters.database.user_repository import UserRepository
from core.adapters.file_storage import FileSystemStorage
from core.adapters.gateway.gateway_client import GatewayClient
from core.adapters.logging.logger_factory import setup_stream_logger
from core.adapters.worker.worker_client import WorkerClient
from desktop.config import config_manager, settings
from desktop.context import AppContext
from manager.application.asset_service import AssetService
from manager.application.device_service import DeviceService
from manager.application.file_service import FileService
from manager.application.material_service import MaterialService
from manager.application.task_service import TaskService
from manager.application.tool_service import ToolService
from manager.application.user_service import UserService


def create_app_context() -> AppContext:
    """Build the production ``AppContext`` from environment config.

    This is the **sole** place in the desktop package that imports concrete
    adapter classes. Every other module receives its dependencies through
    ``AppContext`` or a port typed as a Protocol.
    """
    gateway = GatewayClient.from_config()
    worker = WorkerClient.from_config()
    storage = FileSystemStorage(settings.files_folder_path)
    session_factory = SessionLocal
    app_logger = setup_stream_logger("desktop", logging.INFO, settings.logs_folder_path)

    return AppContext(
        gateway=gateway,
        worker=worker,
        file_storage=storage,
        session_factory=session_factory,
        logger=app_logger,
        settings_reader=settings,
        config_writer=config_manager,
        asset_service=AssetService(
            session_factory=session_factory,
            file_repo_factory=FileRepository,
            material_repo_factory=MaterialRepository,
            tool_repo_factory=ToolRepository,
        ),
        device_service=DeviceService(gateway, worker),
        file_service=FileService(
            worker=worker,
            storage=storage,
            session_factory=session_factory,
            logger=app_logger,
            file_repo_factory=FileRepository,
        ),
        material_service=MaterialService(
            session_factory=session_factory,
            material_repo_factory=MaterialRepository,
        ),
        task_service=TaskService(
            worker=worker,
            session_factory=session_factory,
            task_repo_factory=TaskRepository,
        ),
        tool_service=ToolService(
            session_factory=session_factory,
            tool_repo_factory=ToolRepository,
        ),
        user_service=UserService(
            session_factory=session_factory,
            user_repo_factory=UserRepository,
        ),
    )
