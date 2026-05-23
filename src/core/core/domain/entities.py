from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.domain.task import TASK_DEFAULT_PRIORITY, TASK_EMPTY_NOTE, TaskStatus
from core.domain.types import FileReport, RoleType


@dataclass(slots=True, kw_only=True)
class DomainModel:
    id: int | None = None


@dataclass(slots=True)
class User(DomainModel):
    name: str
    email: str
    password: str
    role: RoleType | str


@dataclass(slots=True)
class Tool(DomainModel):
    name: str
    description: str
    added_at: datetime | None = None


@dataclass(slots=True)
class Material(DomainModel):
    name: str
    description: str
    added_at: datetime | None = None


@dataclass(slots=True)
class File(DomainModel):
    user_id: int
    file_name: str
    file_hash: str
    created_at: datetime | None = None
    report: FileReport | None = None
    user: User | None = None


@dataclass(slots=True)
class Task(DomainModel):
    user_id: int
    file_id: int
    tool_id: int
    material_id: int
    name: str
    note: str = TASK_EMPTY_NOTE
    status: str = TaskStatus.INITIAL.value
    priority: int = TASK_DEFAULT_PRIORITY
    created_at: datetime | None = None
    status_updated_at: datetime | None = None
    admin_id: int | None = None
    cancellation_reason: str | None = None
    file: File | None = None
    tool: Tool | None = None
    material: Material | None = None
    user: User | None = None
    admin: User | None = None
