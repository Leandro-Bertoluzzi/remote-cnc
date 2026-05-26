"""Application context for the Desktop application.

``AppContext`` is the composition root: it holds all infrastructure dependencies.

Views and helpers receive ``AppContext`` (or just the ports they need)
via constructor arguments — never by importing singletons directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.adapters.database.base import SessionLocal
from core.adapters.file_storage import FileSystemStorage
from core.adapters.gateway.gateway_client import GatewayClient
from core.adapters.worker.worker_client import WorkerClient
from core.ports.db_session import DbSession
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient

from desktop.config import FILES_FOLDER_PATH


@dataclass
class AppContext:
    """Container for shared infrastructure dependencies.

    All fields are ports (``typing.Protocol``), never concrete adapter classes.
    Concrete adapters are only referenced in ``create_app_context`` below.
    """

    gateway: IGatewayClient
    worker: IWorkerClient
    file_storage: IFileStorage
    session_factory: Callable[..., DbSession]


def create_app_context() -> AppContext:
    """Build the production ``AppContext`` from environment config.

    This is the **sole** place in the desktop package that imports concrete
    adapter classes. Every other module receives its dependencies through
    ``AppContext`` or a port typed as a Protocol.
    """
    return AppContext(
        gateway=GatewayClient.from_config(),
        worker=WorkerClient.from_config(),
        file_storage=FileSystemStorage(FILES_FOLDER_PATH),
        session_factory=SessionLocal,
    )
