from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.adapters.database.base import Base
from core.domain.task import TASK_DEFAULT_PRIORITY, TASK_EMPTY_NOTE, VALID_ROLES, TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), init=False)

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    note: Mapped[str] = mapped_column(String(150), default=TASK_EMPTY_NOTE)
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.INITIAL.value)
    priority: Mapped[int] = mapped_column(Integer, default=TASK_DEFAULT_PRIORITY)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=datetime.now)
    status_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, init=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(150), init=False)

    admin: Mapped["User"] = relationship(foreign_keys=[admin_id], default=None, init=False)
    file: Mapped["File"] = relationship(back_populates="tasks", init=False)
    tool: Mapped["Tool"] = relationship(back_populates="tasks", init=False)
    material: Mapped["Material"] = relationship(back_populates="tasks", init=False)
    user: Mapped["User"] = relationship(back_populates="tasks", foreign_keys=[user_id], init=False)

    def __repr__(self):
        return f"<Task: {self.name}, status: {self.status}, created at: {self.created_at}>"


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    file_name: Mapped[str] = mapped_column(String(150))
    file_hash: Mapped[str] = mapped_column(String(150))
    report: Mapped[Optional[JSON]] = mapped_column(JSON, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=datetime.now)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="file", default_factory=list, init=False
    )
    user: Mapped["User"] = relationship(back_populates="files", init=False)

    def __repr__(self):
        return f"<File: {self.file_name}, user ID: {self.user_id}, created at: {self.created_at}>"


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(150))
    added_at: Mapped[datetime] = mapped_column(DateTime, default_factory=datetime.now)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="tool", default_factory=list, init=False
    )

    def __repr__(self):
        return f"<Tool: {self.name}, description: {self.description}, added at: {self.added_at}>"


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(150))
    added_at: Mapped[datetime] = mapped_column(DateTime, default_factory=datetime.now)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="material", default_factory=list, init=False
    )

    def __repr__(self):
        return (
            f"<Material: {self.name}, description: {self.description}, added at: {self.added_at}>"
        )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10))

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user", foreign_keys="Task.user_id", default_factory=list, init=False
    )
    files: Mapped[list["File"]] = relationship(
        back_populates="user", default_factory=list, init=False
    )

    def __repr__(self):
        return f"<User: {self.name}, email: {self.email}, role: {self.role}>"


__all__ = [
    "TaskStatus",
    "VALID_ROLES",
    "TASK_EMPTY_NOTE",
    "TASK_DEFAULT_PRIORITY",
    "Task",
    "File",
    "Tool",
    "Material",
    "User",
]
