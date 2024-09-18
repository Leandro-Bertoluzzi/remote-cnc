from core.grbl.types import ParserState, Status
from pydantic import BaseModel
from typing import Optional, Literal


class WorkerTaskResponseModel(BaseModel):
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


class WorkerOnResponseModel(BaseModel):
    is_on: bool


class WorkerPausedResponseModel(BaseModel):
    paused: bool


class DeviceEnabledResponseModel(BaseModel):
    enabled: bool


class WorkerAvailableResponseModel(BaseModel):
    enabled: bool
    running: bool
    available: bool
