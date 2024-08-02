from config import SERIAL_BAUDRATE, SERIAL_PORT
from core.worker.workerStatusManager import WorkerStoreAdapter
from core.worker.scheduler import app, executeTask
import core.worker.utils as worker
from core.grbl.types import ParserState, Status
from core.utils.storage import add_value_with_id
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetUserDep, GetAdminDep
from pydantic import BaseModel
from typing import Optional, Literal

workerRoutes = APIRouter(prefix="/worker", tags=["Worker"])


class TaskWorkerResponseModel(BaseModel):
    success: str
    worker_task_id: str


class TaskStatusResponseModel(BaseModel):
    status: Literal['PENDING', 'STARTED', 'RETRY', 'FAILURE', 'SUCCESS', 'PROGRESS']
    sent_lines: Optional[int]
    processed_lines: Optional[int]
    total_lines: Optional[int]
    cnc_status: Optional[Status]
    cnc_parserstate: Optional[ParserState]
    result: Optional[bool]
    error: Optional[str]


class WorkerStatusResponseModel(BaseModel):
    connected: bool
    running: bool
    stats: dict
    registered_tasks: Optional[worker.WorkerTaskList]
    active_tasks: Optional[worker.WorkerTaskList]


@workerRoutes.post('/task/{db_task_id}')
def send_task_to_worker(
    user: GetAdminDep,
    db_task_id: int
) -> TaskWorkerResponseModel:
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    if not WorkerStoreAdapter.is_device_enabled():
        raise HTTPException(400, detail='Equipo deshabilitado')

    if worker.is_worker_running():
        raise HTTPException(400, detail='Equipo ocupado: Hay una tarea en progreso')

    worker_task = executeTask.delay(
        db_task_id,
        SERIAL_PORT,
        SERIAL_BAUDRATE
    )
    add_value_with_id('task', id=db_task_id, value=worker_task.task_id)

    return {
        'success': 'Se solicitó con éxito la ejecución de la tarea, debería comenzar en breve',
        'worker_task_id': worker_task.task_id
    }


@workerRoutes.get('/status/{worker_task_id}')
def get_worker_task_status(
    user: GetUserDep,
    worker_task_id: str
) -> TaskStatusResponseModel:
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    try:
        task_state = app.AsyncResult(worker_task_id)
        task_info = task_state.info
        task_status = task_state.status
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    response = {
        'status': task_status
    }

    if task_state.failed():
        # If the task raised an exception, 'info' will be the exception instance
        response['error'] = str(task_info)
        return response

    if task_status == 'PROGRESS':
        response['sent_lines'] = task_info.get('sent_lines')
        response['processed_lines'] = task_info.get('processed_lines')
        response['total_lines'] = task_info.get('total_lines')
        response['cnc_status'] = task_info.get('status')
        response['cnc_parserstate'] = task_info.get('parserstate')
        return response

    if task_state.result:
        response['result'] = task_state.result
    return response


@workerRoutes.get('/check/on')
def check_worker_on(user: GetUserDep):
    """Returns whether the worker process is running.
    """
    return {'is_on': worker.is_worker_on()}


@workerRoutes.get('/check/running')
def check_worker_running(user: GetUserDep):
    """Returns whether the worker process is working on a task.
    """
    return {'running': worker.is_worker_running()}


@workerRoutes.get('/check/available')
def check_worker_available(user: GetUserDep):
    """Returns whether the worker process is available to start working on a task.
    """
    enabled = WorkerStoreAdapter.is_device_enabled()
    running = worker.is_worker_running()
    return {
        'enabled': enabled,
        'running': running,
        'available': enabled and not running
    }


@workerRoutes.get('/status')
def get_worker_status(user: GetUserDep) -> WorkerStatusResponseModel:
    """Returns the worker status.
    """
    return worker.get_worker_status()


@workerRoutes.put('/pause/{paused}')
def set_worker_paused(
    user: GetAdminDep,
    paused: int
):
    """Pauses or resume the device.
    """
    if paused != 0:
        WorkerStoreAdapter.request_pause()
        success = 'Se envió la solicitud para pausar la tarea'
    else:
        WorkerStoreAdapter.request_resume()
        success = 'Se envió la solicitud para retomar la tarea'
    return {
        'success': success,
        'paused': WorkerStoreAdapter.is_device_paused()
    }


@workerRoutes.get('/pause')
def check_worker_paused(user: GetUserDep):
    """Checks if the worker is paused
    """
    return {'paused': WorkerStoreAdapter.is_device_paused()}


@workerRoutes.put('/device/{enabled}')
def set_device_enabled(
    user: GetAdminDep,
    enabled: int
):
    """Enables or disables the device.
    """
    WorkerStoreAdapter.set_device_enabled(enabled != 0)
    return {'enabled': WorkerStoreAdapter.is_device_enabled()}


@workerRoutes.get('/device/status')
def get_device_status(user: GetUserDep):
    """Returns the device status (enabled/disabled).
    """
    return {'enabled': WorkerStoreAdapter.is_device_enabled()}
