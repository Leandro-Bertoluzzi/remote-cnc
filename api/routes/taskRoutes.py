from core.database.repositories.taskRepository import TaskRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponseModel
from schemas.tasks import TaskCreateModel, TaskUpdateModel, TaskUpdateStatusModel, \
    TaskResponseModel
from services.utilities import serializeList

taskRoutes = APIRouter(prefix="/tasks", tags=["Tasks"])


@taskRoutes.get('')
@taskRoutes.get('/')
def get_tasks_by_user(
    user: GetUserDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponseModel]:
    repository = TaskRepository(db_session)
    return serializeList(repository.get_all_tasks_from_user(user.id, status))


@taskRoutes.get('/all')
def get_tasks_from_all_users(
    admin: GetAdminDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponseModel]:
    repository = TaskRepository(db_session)
    return serializeList(repository.get_all_tasks(status))


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
        return repository.create_task(
            user.id,
            fileId,
            toolId,
            materialId,
            taskName,
            taskNote
        )
    except Exception as error:
        raise HTTPException(400, detail=str(error))


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
        return repository.update_task_status(
            task_id,
            taskStatus,
            admin_id,
            cancellationReason
        )
    except Exception as error:
        raise HTTPException(400, detail=str(error))


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
        return repository.update_task(
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


@taskRoutes.delete('/{task_id}')
def remove_existing_task(
    task_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> GenericResponseModel:
    try:
        repository = TaskRepository(db_session)
        repository.remove_task(task_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'La tarea fue eliminada con éxito'}
