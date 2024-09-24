from core.grbl.types import ParserState, Status
from pydantic import BaseModel
from typing import Optional, Literal


class WorkerTaskResponse(BaseModel):
    worker_task_id: str


class TaskStatusResponse(BaseModel):
    status: Literal['PENDING', 'STARTED', 'RETRY', 'FAILURE', 'SUCCESS', 'PROGRESS']
    sent_lines: Optional[int]
    processed_lines: Optional[int]
    total_lines: Optional[int]
    cnc_status: Optional[Status]
    cnc_parserstate: Optional[ParserState]
    result: Optional[bool]
    error: Optional[str]


class WorkerOnResponse(BaseModel):
    is_on: bool


class WorkerPausedResponse(BaseModel):
    paused: bool


class DeviceEnabledResponse(BaseModel):
    enabled: bool


class WorkerAvailableResponse(BaseModel):
    enabled: bool
    running: bool
    available: bool
