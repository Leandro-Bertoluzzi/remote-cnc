from typing import Annotated

from core.adapters.database.base import SessionLocal
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
from fastapi import Depends


def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


# Type definition
GetDbSession = Annotated[DbSession, Depends(get_db)]


def get_file_repository(db_session: GetDbSession) -> IFileRepository:
    return FileRepository(db_session)


def get_task_repository(db_session: GetDbSession) -> ITaskRepository:
    return TaskRepository(db_session)


def get_user_repository(db_session: GetDbSession) -> IUserRepository:
    return UserRepository(db_session)


def get_material_repository(db_session: GetDbSession) -> IMaterialRepository:
    return MaterialRepository(db_session)


def get_tool_repository(db_session: GetDbSession) -> IToolRepository:
    return ToolRepository(db_session)


# Type definitions
GetFileRepository = Annotated[IFileRepository, Depends(get_file_repository)]
GetTaskRepository = Annotated[ITaskRepository, Depends(get_task_repository)]
GetUserRepository = Annotated[IUserRepository, Depends(get_user_repository)]
GetMaterialRepository = Annotated[IMaterialRepository, Depends(get_material_repository)]
GetToolRepository = Annotated[IToolRepository, Depends(get_tool_repository)]
