from core.database.repositories.taskRepository import TaskRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponse
from schemas.tasks import TaskCreate, TaskUpdate, TaskUpdateStatus, \
    TaskResponse

taskRoutes = APIRouter(prefix="/tasks", tags=["Tasks"])


@taskRoutes.get('')
@taskRoutes.get('/')
def get_tasks_by_user(
    user: GetUserDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponse]:
    repository = TaskRepository(db_session)
    tasks = repository.get_all_tasks_from_user(user.id, status)

    return [TaskResponse.from_orm(task) for task in tasks]


@taskRoutes.get('/all')
def get_tasks_from_all_users(
    admin: GetAdminDep,
    db_session: GetDbSession,
    status: str = 'all'
) -> list[TaskResponse]:
    repository = TaskRepository(db_session)
    tasks = repository.get_all_tasks(status)

    return [TaskResponse.from_orm(task) for task in tasks]


@taskRoutes.post('', response_model=TaskResponse)
@taskRoutes.post('/', response_model=TaskResponse)
def create_new_task(
    request: TaskCreate,
    user: GetUserDep,
    db_session: GetDbSession
):
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


@taskRoutes.put('/{task_id}/status', response_model=TaskResponse)
def update_existing_task_status(
    task_id: int,
    request: TaskUpdateStatus,
    user: GetUserDep,
    db_session: GetDbSession
):
    taskStatus = request.status
    cancellationReason = request.cancellation_reason

    admin_id = user.id if user.role == 'admin' else None

    try:
        repository = TaskRepository(db_session)
        result = repository.update_task_status(
            task_id,
            taskStatus,
            admin_id,
            cancellationReason
        )
        return TaskResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@taskRoutes.put('/{task_id}', response_model=TaskResponse)
def update_existing_task(
    task_id: int,
    request: TaskUpdate,
    user: GetUserDep,
    db_session: GetDbSession
):
    fileId = request.file_id
    toolId = request.tool_id
    materialId = request.material_id
    taskName = request.name
    taskNote = request.note
    taskPriority = request.priority

    try:
        repository = TaskRepository(db_session)
        result = repository.update_task(
            task_id,
            user.id,
            fileId,
            toolId,
            materialId,
            taskName,
            taskNote,
            taskPriority
        )
        return TaskResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@taskRoutes.delete('/{task_id}', response_model=GenericResponse)
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
