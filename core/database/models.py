from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import List, Literal, Optional
from .base import Base

# Enum values
TASK_PENDING_APPROVAL_STATUS = 'pending_approval'
TASK_ON_HOLD_STATUS = 'on_hold'
TASK_IN_PROGRESS_STATUS = 'in_progress'
TASK_FINISHED_STATUS = 'finished'
TASK_FAILED_STATUS = 'failed'
TASK_CANCELLED_STATUS = 'cancelled'
TASK_APPROVED_STATUS = TASK_ON_HOLD_STATUS

VALID_STATUSES = [
    TASK_PENDING_APPROVAL_STATUS,
    TASK_ON_HOLD_STATUS,
    TASK_IN_PROGRESS_STATUS,
    TASK_FINISHED_STATUS,
    TASK_FAILED_STATUS,
    TASK_CANCELLED_STATUS
]

VALID_ROLES = ['user', 'admin']

# Constants
TASK_EMPTY_NOTE = ''
TASK_DEFAULT_PRIORITY = 0
TASK_INITIAL_STATUS = TASK_PENDING_APPROVAL_STATUS

# Types
StatusType = Literal[
    'pending_approval',
    'on_hold',
    'in_progress',
    'finished',
    'failed',
    'cancelled'
]

RoleType = Literal['user', 'admin']


class Task(Base):
    __tablename__ = 'tasks'

    # Foreign keys
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    file_id: Mapped[Optional[int]] = mapped_column(ForeignKey('files.id'))
    tool_id: Mapped[Optional[int]] = mapped_column(ForeignKey('tools.id'))
    material_id: Mapped[Optional[int]] = mapped_column(ForeignKey('materials.id'))
    admin_id: Mapped[int] = mapped_column(ForeignKey('users.id'), init=False, nullable=True)
    # Object attributes
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    note: Mapped[str] = mapped_column(String(150), default=TASK_EMPTY_NOTE)
    status: Mapped[str] = mapped_column(String(50), default=TASK_INITIAL_STATUS)
    priority: Mapped[int] = mapped_column(Integer, default=TASK_DEFAULT_PRIORITY)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    status_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, init=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(150), init=False)

    # Virtual columns
    admin: Mapped["User"] = relationship(
        foreign_keys=[admin_id],
        default=None,
        init=False
    )
    file: Mapped["File"] = relationship(back_populates="tasks", init=False)
    tool: Mapped["Tool"] = relationship(back_populates="tasks", init=False)
    material: Mapped["Material"] = relationship(back_populates="tasks", init=False)
    user: Mapped["User"] = relationship(
        back_populates="tasks",
        foreign_keys=[user_id],
        init=False
    )

    def __repr__(self):
        return f"<Task: {self.name}, status: {self.status}, created at: {self.created_at}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "user": self.user.name,
            "file_id": self.file_id,
            "file": self.file.file_name,
            "tool_id": self.tool_id,
            "tool": self.tool.name,
            "material_id": self.material_id,
            "material": self.material.name,
            "note": self.note,
            "created_at": self.created_at,
            "status_updated_at": self.status_updated_at,
            "admin_id": self.admin_id,
            "admin": "" if not self.admin else self.admin.name,
            "cancellation_reason": self.cancellation_reason
        }


class File(Base):
    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    # Foreign keys
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'))
    # Other attributes
    file_name: Mapped[str] = mapped_column(String(150))
    file_hash: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    # Virtual columns
    tasks: Mapped[List["Task"]] = relationship(
        back_populates='file',
        default_factory=list,
        init=False
    )
    user: Mapped["User"] = relationship(back_populates="files", init=False)

    def __repr__(self):
        return (
            f"<File: {self.file_name}, "
            f"user ID: {self.user_id}, created at: {self.created_at}>"
        )

    def serialize(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "user_id": self.user_id,
            "user": self.user.name,
            "file_hash": self.file_hash,
            "created_at": self.created_at
        }


class Tool(Base):
    __tablename__ = 'tools'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(150))
    added_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now())

    # Virtual columns
    tasks: Mapped[List["Task"]] = relationship(
        back_populates='tool',
        default_factory=list,
        init=False
    )

    def __repr__(self):
        return f"<Tool: {self.name}, description: {self.description}, added at: {self.added_at}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "added_at": self.added_at
        }


class Material(Base):
    __tablename__ = 'materials'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(150))
    added_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now())

    # Virtual columns
    tasks: Mapped[List["Task"]] = relationship(
        back_populates='material',
        default_factory=list,
        init=False
    )

    def __repr__(self):
        return (
            f"<Material: {self.name}, description: {self.description}, added at: {self.added_at}>"
        )

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "added_at": self.added_at
        }


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10))

    # Virtual columns
    tasks: Mapped[List["Task"]] = relationship(
        back_populates='user',
        foreign_keys='Task.user_id',
        default_factory=list,
        init=False
    )
    files: Mapped[List["File"]] = relationship(
        back_populates='user',
        default_factory=list,
        init=False
    )

    def __repr__(self):
        return f"<User: {self.name}, email: {self.email}, role: {self.role}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role
        }
