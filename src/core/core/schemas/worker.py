from typing import Literal, Optional

from pydantic import BaseModel

from core.utilities.grbl.types import ParserState, Status


class WorkerTaskResponse(BaseModel):
    worker_task_id: str


class TaskStatusResponse(BaseModel):
    status: Literal["PENDING", "STARTED", "RETRY", "FAILURE", "SUCCESS", "PROGRESS"]
    sent_lines: Optional[int] = None
    processed_lines: Optional[int] = None
    total_lines: Optional[int] = None
    cnc_status: Optional[Status] = None
    cnc_parserstate: Optional[ParserState] = None
    result: Optional[bool] = None
    error: Optional[str] = None


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
