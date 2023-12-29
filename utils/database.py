try:
    from ..database.base import Session
    from ..database.models import TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
    from ..database.repositories.fileRepository import FileRepository
    from ..database.repositories.materialRepository import MaterialRepository
    from ..database.repositories.taskRepository import TaskRepository
    from ..database.repositories.toolRepository import ToolRepository
    from ..database.repositories.userRepository import UserRepository
except ImportError:
    from database.base import Session
    from database.models import TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
    from database.repositories.fileRepository import FileRepository
    from database.repositories.materialRepository import MaterialRepository
    from database.repositories.taskRepository import TaskRepository
    from database.repositories.toolRepository import ToolRepository
    from database.repositories.userRepository import UserRepository
from typing import Optional


def session_context(func):
    def wrapper(*args, **kwargs):
        with Session() as session:
            return func(session, *args, **kwargs)
    return wrapper

###################################################################
#                              TOOLS                              #
###################################################################


@session_context
def create_tool(session, name, description):
    tool_repository = ToolRepository(session)
    new_tool = tool_repository.create_tool(name=name, description=description)
    return new_tool


@session_context
def get_all_tools(session):
    tool_repository = ToolRepository(session)
    tools = tool_repository.get_all_tools()
    return tools


@session_context
def get_tool_by_id(session, tool_id):
    tool_repository = ToolRepository(session)
    tool = tool_repository.get_tool_by_id(tool_id)
    return tool


@session_context
def update_tool(session, tool_id, name, description):
    tool_repository = ToolRepository(session)
    updated_tool = tool_repository.update_tool(tool_id, name, description)
    return updated_tool


@session_context
def remove_tool(session, tool_id):
    tool_repository = ToolRepository(session)
    tool_repository.remove_tool(tool_id)

###################################################################
#                            MATERIALS                            #
###################################################################


@session_context
def create_material(session, name, description):
    material_repository = MaterialRepository(session)
    new_material = material_repository.create_material(name=name, description=description)
    return new_material


@session_context
def get_all_materials(session):
    material_repository = MaterialRepository(session)
    materials = material_repository.get_all_materials()
    return materials


@session_context
def update_material(session, material_id, name, description):
    material_repository = MaterialRepository(session)
    updated_material = material_repository.update_material(material_id, name, description)
    return updated_material


@session_context
def remove_material(session, material_id):
    material_repository = MaterialRepository(session)
    material_repository.remove_material(material_id)

###################################################################
#                              USERS                              #
###################################################################


@session_context
def get_user_by_email(session, email):
    user_repository = UserRepository(session)
    user = user_repository.get_user_by_email(email)
    return user


@session_context
def create_user(session, name, email, password, role):
    user_repository = UserRepository(session)
    new_user = user_repository.create_user(name, email, password, role)
    return new_user


@session_context
def get_all_users(session):
    user_repository = UserRepository(session)
    users = user_repository.get_all_users()
    return users


@session_context
def update_user(session, user_id, name, email, role):
    user_repository = UserRepository(session)
    updated_user = user_repository.update_user(user_id, name, email, role)
    return updated_user


@session_context
def remove_user(session, user_id):
    user_repository = UserRepository(session)
    user_repository.remove_user(user_id)

###################################################################
#                              FILES                              #
###################################################################


@session_context
def create_file(session, user_id, file_name, file_name_saved):
    file_repository = FileRepository(session)
    new_file = file_repository.create_file(user_id, file_name, file_name_saved)
    return new_file


@session_context
def get_all_files_from_user(session, user_id):
    file_repository = FileRepository(session)
    files = file_repository.get_all_files_from_user(user_id)
    return files


@session_context
def get_all_files(session):
    file_repository = FileRepository(session)
    files = file_repository.get_all_files()
    return files


@session_context
def get_file_by_id(session, file_id):
    file_repository = FileRepository(session)
    file = file_repository.get_file_by_id(file_id)
    return file


@session_context
def update_file(session, file_id, user_id, file_name, file_name_saved):
    file_repository = FileRepository(session)
    file = file_repository.update_file(file_id, user_id, file_name, file_name_saved)
    return file


@session_context
def remove_file(session, file_id):
    file_repository = FileRepository(session)
    file_repository.remove_file(file_id)

###################################################################
#                              TASKS                              #
###################################################################


@session_context
def create_task(
    session,
    user_id: int,
    file_id: int,
    tool_id: int,
    material_id: int,
    name: str,
    note: str
):
    task_repository = TaskRepository(session)
    new_task = task_repository.create_task(
        user_id,
        file_id,
        tool_id,
        material_id,
        name,
        note
    )
    return new_task


@session_context
def get_all_tasks_from_user(session, user_id: int, status: str = 'all'):
    task_repository = TaskRepository(session)
    tasks = task_repository.get_all_tasks_from_user(user_id, status)
    return tasks


@session_context
def get_all_tasks(session, status: str = 'all'):
    task_repository = TaskRepository(session)
    tasks = task_repository.get_all_tasks(status)
    return tasks


@session_context
def get_next_task(session):
    task_repository = TaskRepository(session)
    task = task_repository.get_next_task()
    return task


@session_context
def update_task(
    session,
    task_id: int,
    user_id: int,
    file_id: int,
    tool_id: int,
    material_id: int,
    name: str,
    note: str,
    priority: int
):
    task_repository = TaskRepository(session)
    task = task_repository.update_task(
        task_id,
        user_id,
        file_id,
        tool_id,
        material_id,
        name,
        note,
        priority
    )
    return task


@session_context
def update_task_status(
    session,
    task_id: int,
    status: str,
    admin_id: Optional[int] = None,
    cancellation_reason: str = ""
):
    task_repository = TaskRepository(session)
    task = task_repository.update_task_status(
        task_id,
        status,
        admin_id,
        cancellation_reason
    )
    return task


@session_context
def remove_task(session, task_id):
    task_repository = TaskRepository(session)
    task_repository.remove_task(task_id)


@session_context
def are_there_tasks_with_status(session, status: str) -> bool:
    task_repository = TaskRepository(session)
    tasks = task_repository.get_all_tasks(status=status)
    return bool(tasks)


def are_there_pending_tasks() -> bool:
    return are_there_tasks_with_status(TASK_APPROVED_STATUS)


def are_there_tasks_in_progress() -> bool:
    return are_there_tasks_with_status(TASK_REJECTED_STATUS)
