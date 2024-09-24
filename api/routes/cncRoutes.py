from config import SERIAL_PORT, SERIAL_BAUDRATE
from core.worker.workerStatusManager import WorkerStoreAdapter
from core.worker.scheduler import cncServer, COMMANDS_CHANNEL
import core.worker.utils as worker
import core.grbl.grblUtils as grblUtils
from core.utils.serial import SerialService
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep
from middleware.pubSubMiddleware import GetPubSub
from schemas.cnc import CncCommand, CncJogCommand, CncJogResponse
from schemas.worker import WorkerTaskResponse
from schemas.general import GenericResponse

cncRoutes = APIRouter(prefix="/cnc", tags=["CNC"])


@cncRoutes.get('/ports')
def get_available_ports(admin: GetAdminDep):
    try:
        available_ports = SerialService.get_ports()
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'ports': available_ports}


@cncRoutes.post('/server', response_model=WorkerTaskResponse)
def start_cnc_server(admin: GetAdminDep):
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    if not WorkerStoreAdapter.is_device_enabled():
        raise HTTPException(400, detail='Equipo deshabilitado')

    if worker.is_worker_running():
        raise HTTPException(400, detail='Equipo ocupado: Hay una tarea en progreso')

    worker_task = cncServer.delay(
        SERIAL_PORT,
        SERIAL_BAUDRATE
    )

    return {'worker_task_id': worker_task.task_id}


@cncRoutes.delete('/server', response_model=GenericResponse)
async def stop_cnc_server(admin: GetAdminDep, redis: GetPubSub):
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    # TODO: Improve this...
    await redis.publish(COMMANDS_CHANNEL, 'M2')

    return {'success': 'Se finalizó la conexión con el CNC'}


@cncRoutes.post('/command', response_model=GenericResponse)
async def send_code_to_execute(
    request: CncCommand,
    admin: GetAdminDep,
    redis: GetPubSub
):
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    if not worker.is_worker_running():
        raise HTTPException(400, detail='Debe iniciar la conexión con el servidor CNC')

    code = request.command
    await redis.publish(COMMANDS_CHANNEL, code)

    return {'success': 'El comando fue enviado para su ejecución'}


@cncRoutes.post('/jog', response_model=CncJogResponse)
async def send_jog_command(
    admin: GetAdminDep,
    redis: GetPubSub,
    request: CncJogCommand,
    machine: bool = False
):
    if not worker.is_worker_on():
        raise HTTPException(400, detail='Worker desconectado')

    if not worker.is_worker_running():
        raise HTTPException(400, detail='Debe iniciar la conexión con el servidor CNC')

    code = grblUtils.build_jog_command(
        request.x,
        request.y,
        request.z,
        request.feedrate,
        units=request.units,
        distance_mode=request.mode,
        machine_coordinates=machine
    )
    await redis.publish(COMMANDS_CHANNEL, code)

    return {'command': code}
