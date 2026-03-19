from core.schemas.worker import (
    WorkerAvailableResponse,
    WorkerOnResponse,
    WorkerTaskResponse,
)
from core.utilities.worker.workerClient import WorkerStatus
from fastapi import APIRouter, HTTPException

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.gatewayMiddleware import GetGateway
from api.middleware.workerMiddleware import GetWorker

workerRoutes = APIRouter(prefix="/worker", tags=["Worker"])


@workerRoutes.post("/task/{db_task_id}", response_model=WorkerTaskResponse)
def execute_task(user: GetAdminDep, db_task_id: int, worker: GetWorker, gateway: GetGateway):
    if not worker.is_on():
        raise HTTPException(400, detail="Worker desconectado")

    if not gateway.is_gateway_running():
        raise HTTPException(400, detail="Gateway CNC no disponible")

    if gateway.get_active_session() is not None:
        raise HTTPException(400, detail="El CNC está en uso por otra sesión")

    if worker.is_running():
        raise HTTPException(400, detail="Equipo ocupado: Hay una tarea en progreso")

    worker_task_id = worker.send_task(db_task_id)
    return {"worker_task_id": worker_task_id}


@workerRoutes.get("/check/on", response_model=WorkerOnResponse)
def check_worker_on(user: GetUserDep, worker: GetWorker):
    """Returns whether the worker process is running."""
    return {"is_on": worker.is_on()}


@workerRoutes.get("/check/available", response_model=WorkerAvailableResponse)
def check_worker_available(user: GetUserDep, worker: GetWorker, gateway: GetGateway):
    """Returns whether the worker process is available to start working on a task."""
    gateway_ready = gateway.is_gateway_running() and gateway.get_active_session() is None
    running = worker.is_running()
    return {
        "enabled": gateway_ready,
        "running": running,
        "available": gateway_ready and not running,
    }


@workerRoutes.get("/status")
def get_worker_status(user: GetUserDep, worker: GetWorker) -> WorkerStatus:
    """Returns the worker status."""
    if not worker.is_on():
        raise HTTPException(400, detail="Worker desconectado")
    return worker.get_status()
