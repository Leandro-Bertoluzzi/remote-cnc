"""Repository factories for the desktop service layer."""

from __future__ import annotations

from core.adapters.database.file_repository import FileRepository
from core.adapters.database.material_repository import MaterialRepository
from core.adapters.database.task_repository import TaskRepository
from core.adapters.database.tool_repository import ToolRepository
from core.adapters.database.user_repository import UserRepository
from core.ports.db_session import DbSession
from core.ports.file_repository import IFileRepository
from core.ports.material_repository import IMaterialRepository
from core.ports.task_repository import ITaskRepository
from core.ports.tool_repository import IToolRepository
from core.ports.user_repository import IUserRepository


def get_file_repository(session: DbSession) -> IFileRepository:
    return FileRepository(session)


def get_task_repository(session: DbSession) -> ITaskRepository:
    return TaskRepository(session)


def get_user_repository(session: DbSession) -> IUserRepository:
    return UserRepository(session)


def get_material_repository(session: DbSession) -> IMaterialRepository:
    return MaterialRepository(session)


def get_tool_repository(session: DbSession) -> IToolRepository:
    return ToolRepository(session)
