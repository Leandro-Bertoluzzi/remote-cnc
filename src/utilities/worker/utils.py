from config import SERIAL_BAUDRATE, SERIAL_PORT
from functools import reduce
from typing import Any, Optional
from typing_extensions import TypedDict
from utilities.storage import add_value_with_id
from utilities.worker.scheduler import app, executeTask

# Types definition
RegisteredTaskList = dict[str, list[str]]
ActiveTaskList = dict[str, list[Any]]
WorkerStatus = TypedDict('WorkerStatus', {
    'connected': bool,
    'running': bool,
    'stats': dict,
    'registered_tasks': Optional[RegisteredTaskList],
    'active_tasks': Optional[ActiveTaskList]
})


def is_worker_on():
    """Returns whether the worker process is running.
    """
    inspector = app.control.inspect()
    return not not inspector.ping()


def is_worker_running():
    """Returns whether the worker process is working on a task.
    """
    inspector = app.control.inspect()
    active_tasks = inspector.active()
    if not active_tasks:
        return False
    tasks_count = reduce(
        lambda x, tasks: x + len(tasks),
        active_tasks.values(),
        0
    )
    return tasks_count > 0


def get_worker_status() -> WorkerStatus:
    """Returns the worker status.
    """
    inspector = app.control.inspect()

    connected = is_worker_on()
    running = is_worker_running()
    stats = inspector.stats()
    registered_tasks = inspector.registered()
    active_tasks = inspector.active()
    result = {
        'connected': connected,
        'running': running,
        'stats': stats,
        'registered_tasks': registered_tasks,
        'active_tasks': active_tasks
    }
    return result


def send_task_to_worker(db_task_id: int) -> str:
    """Request the task to be executed by the worker.
    """
    worker_task = executeTask.delay(
        db_task_id,
        SERIAL_PORT,
        SERIAL_BAUDRATE
    )
    add_value_with_id('task', id=db_task_id, value=worker_task.task_id)

    return worker_task.task_id
