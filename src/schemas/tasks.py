from database.types import StatusType
import datetime
from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    name: str
    file_id: int
    tool_id: int
    material_id: int
    note: Optional[str] = ''


class TaskUpdateStatus(BaseModel):
    status: StatusType
    cancellation_reason: Optional[str] = ''


class TaskUpdate(BaseModel):
    file_id: Optional[int] = None
    tool_id: Optional[int] = None
    material_id: Optional[int] = None
    name: Optional[str] = None
    priority: Optional[int] = None
    note: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    name: str
    status: str
    priority: int
    user_id: int
    file_id: int
    tool_id: int
    material_id: int
    note: str
    admin_id: Optional[int] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        orm_mode = True
