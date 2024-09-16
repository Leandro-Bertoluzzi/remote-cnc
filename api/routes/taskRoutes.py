from core.database.models import StatusType
from core.database.repositories.taskRepository import TaskRepository
import datetime
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel
from typing import Optional
from services.utilities import serializeList

taskRoutes = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreateModel(BaseModel):
    name: str
    file_id: int
    tool_id: int
    material_id: int
    note: Optional[str] = ''


class TaskUpdateStatusModel(BaseModel):
    status: StatusType
    cancellation_reason: Optional[str] = ''


class TaskUpdateModel(BaseModel):
    file_id: Optional[int] = None
    tool_id: Optional[int] = None
    material_id: Optional[int] = None
    name: Optional[str] = None
    priority: Optional[int] = None
    note: Optional[str] = None


class TaskResponseModel(BaseModel):
    id: int
    name: str
    status: str
    priority: int
    user_id: int
    file_id: int
    tool_id: int
    material_id: int
    note: str
    admin_id: Optional[int] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime.datetime


@taskRoutes.get('')
@taskRoutes.get('/')
def get_tasks_by_user(
    user: GetUserDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponseModel]:
    repository = TaskRepository(db_session)
    tasks = serializeList(repository.get_all_tasks_from_user(user.id, status))
    return tasks


@taskRoutes.get('/all')
def get_tasks_from_all_users(
    admin: GetAdminDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponseModel]:
    repository = TaskRepository(db_session)
    tasks = serializeList(repository.get_all_tasks(status))
    return tasks


@taskRoutes.post('')
@taskRoutes.post('/')
def create_new_task(
    request: TaskCreateModel,
    user: GetUserDep,
    db_session: GetDbSession
) -> TaskResponseModel:
    fileId = request.file_id
    toolId = request.tool_id
    materialId = request.material_id
    taskName = request.name
    taskNote = request.note

    try:
        repository = TaskRepository(db_session)
        new_task = repository.create_task(
            user.id,
            fileId,
            toolId,
            materialId,
            taskName,
            taskNote
        )
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return new_task


@taskRoutes.put('/{task_id}/status')
def update_existing_task_status(
    task_id: int,
    request: TaskUpdateStatusModel,
    user: GetUserDep,
    db_session: GetDbSession
) -> TaskResponseModel:
    taskStatus = request.status
    cancellationReason = request.cancellation_reason

    admin_id = user.id if user.role == 'admin' else None

    try:
        repository = TaskRepository(db_session)
        updated_task = repository.update_task_status(
            task_id,
            taskStatus,
            admin_id,
            cancellationReason
        )
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return updated_task


@taskRoutes.put('/{task_id}')
def update_existing_task(
    task_id: int,
    request: TaskUpdateModel,
    user: GetUserDep,
    db_session: GetDbSession
) -> TaskResponseModel:
    fileId = request.file_id
    toolId = request.tool_id
    materialId = request.material_id
    taskName = request.name
    taskNote = request.note
    taskPriority = request.priority

    try:
        repository = TaskRepository(db_session)
        updated_task = repository.update_task(
            task_id,
            user.id,
            fileId,
            toolId,
            materialId,
            taskName,
            taskNote,
            taskPriority
        )
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return updated_task


@taskRoutes.delete('/{task_id}')
def remove_existing_task(
    task_id: int,
    user: GetUserDep,
    db_session: GetDbSession
):
    try:
        repository = TaskRepository(db_session)
        repository.remove_task(task_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'La tarea fue eliminada con éxito'}
