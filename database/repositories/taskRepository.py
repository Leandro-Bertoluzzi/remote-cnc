from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.task import Task, TASK_PENDING_APPROVAL_STATUS, TASK_IN_PROGRESS_STATUS, TASK_APPROVED_STATUS, TASK_REJECTED_STATUS, TASK_ON_HOLD_STATUS, TASK_CANCELLED_STATUS
from datetime import datetime

def createTask(
    userId,
    fileId,
    toolId,
    materialId,
    name,
    note
):
    task_args = [
        userId,
        fileId,
        toolId,
        materialId,
        name
    ]

    # Optional arguments
    if note:
        task_args.append(note)

    # Create the task
    newTask = Task(*task_args)

    # Create a new session
    session = Session()

    # Persist data in DB
    session.add(newTask)

    # Commit changes in DB
    try:
        session.commit()
        print('The task was successfully created!')
    except SQLAlchemyError as e:
        raise Exception(f'Error creating the task in the DB: {e}')

    # Close session
    session.close()

    return

def getAllTasksFromUser(user_id: int, status: str = 'all'):
    # Create a new session
    session = Session()

    # Get data from DB
    tasks = []
    try:
        if status == 'all':
            tasks = session.query(Task).filter_by(user_id=user_id).all()
        else:
            tasks = session.query(Task).filter_by(status=status, user_id=user_id).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving tasks from the DB: {e}')

    for task in tasks:
        print(f'## Task: {task.name}')
        print(f'Owner: {task.user.name}')
        print(f'File: {task.file.file_name}')
        print(f'Tool: {task.tool.name}')
        print(f'Material: {task.material.name}')
        print(f'Admin: {"" if not task.admin else task.admin.name}')

    # Close session
    session.close()

    return tasks

def getAllTasks(status: str = 'all'):
    # Create a new session
    session = Session()

    # Get data from DB
    tasks = []
    try:
        if status == 'all':
            tasks = session.query(Task).order_by(Task.priority.asc()).all()
        else:
            tasks = session.query(Task).filter_by(status=status).order_by(Task.priority.asc()).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving tasks from the DB: {e}')

    for task in tasks:
        print(f'## Task: {task.name}')
        print(f'Owner: {task.user.name}')
        print(f'File: {task.file.file_name}')
        print(f'Tool: {task.tool.name}')
        print(f'Material: {task.material.name}')
        print(f'Admin: {"" if not task.admin else task.admin.name}')

    # Close session
    session.close()

    return tasks

def getNextTask():
    # Create a new session
    session = Session()

    # Get data from DB
    try:
        task = session.query(Task).filter_by(status=TASK_ON_HOLD_STATUS).order_by(Task.priority.desc()).first()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving tasks from the DB: {e}')

    print(f'## Task: {task.name}')
    print(f'Owner: {task.user.name}')
    print(f'File: {task.file.file_name}, {task.file.file_path}')
    print(f'Tool: {task.tool.name}')
    print(f'Material: {task.material.name}')
    print(f'Admin: {"" if not task.admin else task.admin.name}')

    # Close session
    session.close()

    return task

def updateTask(
    id,
    userId,
    fileId,
    toolId,
    materialId,
    name,
    note,
    priority
):
    # Create a new session
    session = Session()

    # Get task from DB
    try:
        task = session.query(Task).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for task in the DB: {e}')

    if not task or task.user_id != userId:
        raise Exception(f'Task with ID {id} was not found for this user')

    # Update the task's info
    task.file_id = fileId if fileId else task.file_id
    task.tool_id = toolId if toolId else task.tool_id
    task.material_id = materialId if materialId else task.material_id
    task.name = name if name else task.name
    task.note = note if note else task.note
    task.priority = priority if priority else task.priority

    # Commit changes in DB
    try:
        session.commit()
        print('The task was successfully updated!')
    except Exception as error:
        raise Exception(f'Error updating task with ID {id} in DB')

    # Close session
    session.close()

def updateTaskStatus(id, status, admin_id=None, cancellation_reason=""):
    # Create a new session
    session = Session()

    # Get task from DB
    try:
        task = session.query(Task).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for task in the DB: {e}')

    if not task:
        raise Exception(f'Task with ID {id} was not found for this user')

    approved = task.status == TASK_PENDING_APPROVAL_STATUS and status == TASK_APPROVED_STATUS
    rejected = task.status == TASK_PENDING_APPROVAL_STATUS and status == TASK_REJECTED_STATUS

    task.status = status
    task.status_updated_at = datetime.now()

    if approved or rejected:
        task.admin_id = admin_id

    if status == TASK_PENDING_APPROVAL_STATUS:
        task.admin_id = None
        task.status_updated_at = None

    if status == TASK_CANCELLED_STATUS or rejected:
        task.cancellation_reason = cancellation_reason

    # Commit changes in DB
    try:
        session.commit()
        print('The task status was successfully updated!')
    except SQLAlchemyError as e:
        raise Exception(f'Error updating the task status in the DB: {e}')

    # Close session
    session.close()

def removeTask(id):
    # Create a new session
    session = Session()

    # Get task from DB
    try:
        task = session.query(Task).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for task in the DB: {e}')

    if not task:
        raise Exception(f'Task with ID {id} was not found')

    # Remove the task
    session.delete(task)

    # Commit changes in DB
    try:
        session.commit()
        print('The task was successfully removed!')
    except SQLAlchemyError as e:
        raise Exception(f'Error removing the task from the DB: {e}')

    # Close session
    session.close()

def areThereTasksInStatus(status: str) -> bool:
    # Create a new session
    session = Session()

    tasks = session.query(Task).filter_by(status=status).all()

    # Close session
    session.close()

    return not not tasks

def areTherePendingTasks() -> bool:
    return areThereTasksInStatus(TASK_ON_HOLD_STATUS)

def areThereTasksInProgress() -> bool:
    return areThereTasksInStatus(TASK_IN_PROGRESS_STATUS)
