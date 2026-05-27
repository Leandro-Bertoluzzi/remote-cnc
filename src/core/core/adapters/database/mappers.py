from __future__ import annotations

from typing import cast

from core.adapters.database import models
from core.domain.entities import File, Material, Task, Tool, User
from core.domain.types import RoleType


def to_user_domain(user: models.User | None) -> User | None:
    if user is None:
        return None

    return User(
        id=user.id,
        name=user.name,
        email=user.email,
        password=user.password,
        role=cast(RoleType, user.role),
    )


def to_tool_domain(tool: models.Tool | None) -> Tool | None:
    if tool is None:
        return None

    return Tool(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        added_at=tool.added_at,
    )


def to_material_domain(material: models.Material | None) -> Material | None:
    if material is None:
        return None

    return Material(
        id=material.id,
        name=material.name,
        description=material.description,
        added_at=material.added_at,
    )


def to_file_domain(file: models.File | None, *, include_user: bool = True) -> File | None:
    if file is None:
        return None

    return File(
        id=file.id,
        user_id=file.user_id,
        file_name=file.file_name,
        file_hash=file.file_hash,
        report=file.report,
        created_at=file.created_at,
        user=to_user_domain(file.user) if include_user else None,
    )


def to_task_domain(task: models.Task | None) -> Task | None:
    if task is None:
        return None

    return Task(
        id=task.id,
        user_id=task.user_id,
        file_id=task.file_id,
        tool_id=task.tool_id,
        material_id=task.material_id,
        admin_id=task.admin_id,
        name=task.name,
        note=task.note,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at,
        status_updated_at=task.status_updated_at,
        cancellation_reason=task.cancellation_reason,
        file=to_file_domain(task.file),
        tool=to_tool_domain(task.tool),
        material=to_material_domain(task.material),
        user=to_user_domain(task.user),
        admin=to_user_domain(task.admin),
    )
