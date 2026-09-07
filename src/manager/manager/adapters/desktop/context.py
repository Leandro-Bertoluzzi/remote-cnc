"""Application context for the Desktop application.

``AppContext`` is the composition root: it holds all infrastructure dependencies
and all application-layer service instances.

Views and helpers receive ``AppContext`` (or just the ports they need)
via constructor arguments — never by importing singletons directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.ports.db_session import SessionFactory
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.logger import ILogger
from core.ports.worker_client import IWorkerClient
from manager.adapters.desktop.ports.config_writer import IConfigWriter
from manager.adapters.desktop.ports.settings_reader import ISettingsReader
from manager.application.asset_service import AssetService
from manager.application.device_service import DeviceService
from manager.application.file_service import FileService
from manager.application.material_service import MaterialService
from manager.application.task_service import TaskService
from manager.application.tool_service import ToolService
from manager.application.user_service import UserService


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

    # Configuration ports
    settings_reader: ISettingsReader
    config_writer: IConfigWriter

    # Application services
    asset_service: AssetService
    device_service: DeviceService
    file_service: FileService
    material_service: MaterialService
    task_service: TaskService
    tool_service: ToolService
    user_service: UserService
