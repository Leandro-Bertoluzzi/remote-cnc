"""Gateway domain schemas — Pydantic models for incoming message payloads."""

from __future__ import annotations

from typing import Literal

from core.domain.cnc import JogDistanceMode, JogUnit
from core.domain.gateway import (
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_SOFT_RESET,
    ACTION_STOP,
)
from pydantic import BaseModel, Field

RealtimeAction = Literal[ACTION_PAUSE, ACTION_RESUME, ACTION_STOP, ACTION_SOFT_RESET]  # ty:ignore[invalid-type-form]
QueryType = Literal["status", "parserstate", "settings", "params", "build_info", "help"]


class JogPayload(BaseModel):
    """Validated payload for a ``MSG_JOG`` message."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    feedrate: float = 0.0
    units: JogUnit | None = None
    distance_mode: JogDistanceMode | None = None
    machine_coordinates: bool = False


class RealtimePayload(BaseModel):
    """Validated payload for a ``MSG_REALTIME`` message."""

    action: RealtimeAction


class CommandPayload(BaseModel):
    """Validated payload for a ``MSG_COMMAND`` message."""

    command: str = Field(min_length=1)


class FileStartPayload(BaseModel):
    """Validated payload for a ``MSG_FILE_START`` message."""

    file_path: str = Field(min_length=1)
    task_id: int | None = None
    shared_logger_name: str | None = None


class QueryPayload(BaseModel):
    """Validated payload for a ``MSG_QUERY`` message."""

    query: QueryType
