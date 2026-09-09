from pydantic import BaseModel


class WorkerTaskResponse(BaseModel):
    worker_task_id: str


class WorkerOnResponse(BaseModel):
    is_on: bool


class WorkerAvailableResponse(BaseModel):
    enabled: bool
    running: bool
    available: bool
