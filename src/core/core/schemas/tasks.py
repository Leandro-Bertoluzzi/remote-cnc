import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from core.database.types import StatusType


class TaskCreate(BaseModel):
    name: str
    file_id: int
    tool_id: int
    material_id: int
    note: str = ""


class TaskUpdateStatus(BaseModel):
    status: StatusType
    cancellation_reason: str = ""


class TaskUpdate(BaseModel):
    file_id: Optional[int] = None
    tool_id: Optional[int] = None
    material_id: Optional[int] = None
    name: Optional[str] = None
    priority: Optional[int] = None
    note: Optional[str] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
