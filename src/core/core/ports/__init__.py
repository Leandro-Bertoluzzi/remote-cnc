"""Shared port abstractions for all modules.

See DR-0007 for the architectural rationale.
"""

from core.ports.db_session import DbSession
from core.ports.file_repository import IFileRepository
from core.ports.gateway_client import IGatewayClient
from core.ports.key_value_store import IKeyValueStore
from core.ports.material_repository import IMaterialRepository
from core.ports.priority_queue import IPriorityQueue
from core.ports.pubsub_client import IPubSubClient
from core.ports.task_repository import ITaskRepository
from core.ports.tool_repository import IToolRepository
from core.ports.user_repository import IUserRepository
from core.ports.worker_client import IWorkerClient

__all__ = [
    "DbSession",
    "IFileRepository",
    "IGatewayClient",
    "IKeyValueStore",
    "IMaterialRepository",
    "IPriorityQueue",
    "IPubSubClient",
    "ITaskRepository",
    "IToolRepository",
    "IUserRepository",
    "IWorkerClient",
]
