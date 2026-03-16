from core.database.repositories.taskRepository import TaskRepository
from core.schemas.general import GenericResponse
from core.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate, TaskUpdateStatus
from fastapi import APIRouter

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetDbSession

taskRoutes = APIRouter(prefix="/tasks", tags=["Tasks"])


@taskRoutes.get("")
@taskRoutes.get("/")
def get_tasks_by_user(
    user: GetUserDep, db_session: GetDbSession, status: str = "all"
) -> list[TaskResponse]:
    repository = TaskRepository(db_session)
    tasks = repository.get_all_tasks_from_user(user.id, status)

    return [TaskResponse.model_validate(task) for task in tasks]


@taskRoutes.get("/all")
def get_tasks_from_all_users(
    admin: GetAdminDep, db_session: GetDbSession, status: str = "all"
) -> list[TaskResponse]:
    repository = TaskRepository(db_session)
    tasks = repository.get_all_tasks(status)

    return [TaskResponse.model_validate(task) for task in tasks]


@taskRoutes.post("", response_model=TaskResponse)
@taskRoutes.post("/", response_model=TaskResponse)
def create_new_task(request: TaskCreate, user: GetUserDep, db_session: GetDbSession):
    repository = TaskRepository(db_session)
    return repository.create_task(
        user.id, request.file_id, request.tool_id, request.material_id, request.name, request.note
    )


@taskRoutes.put("/{task_id}/status", response_model=TaskResponse)
def update_existing_task_status(
    task_id: int, request: TaskUpdateStatus, user: GetUserDep, db_session: GetDbSession
):
    admin_id = user.id if user.role == "admin" else None
    repository = TaskRepository(db_session)
    result = repository.update_task_status(
        task_id, request.status, admin_id, request.cancellation_reason
    )
    return TaskResponse.model_validate(result)


@taskRoutes.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(
    task_id: int, request: TaskUpdate, user: GetUserDep, db_session: GetDbSession
):
    repository = TaskRepository(db_session)
    result = repository.update_task(
        task_id,
        user.id,
        request.file_id,
        request.tool_id,
        request.material_id,
        request.name,
        request.note,
        request.priority,
    )
    return TaskResponse.model_validate(result)


@taskRoutes.delete("/{task_id}", response_model=GenericResponse)
def remove_existing_task(task_id: int, user: GetUserDep, db_session: GetDbSession):
    repository = TaskRepository(db_session)
    repository.remove_task(task_id)
    return {"success": "La tarea fue eliminada con éxito"}
