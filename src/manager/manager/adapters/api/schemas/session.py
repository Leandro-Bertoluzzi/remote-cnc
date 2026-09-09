"""Schemas for CNC session management (DR-0002)."""

from typing import Literal, Optional

from pydantic import BaseModel


class SessionAcquireRequest(BaseModel):
    """Body for POST /cnc/session."""

    client_type: Literal["web", "desktop", "worker"] = "web"


class SessionResponse(BaseModel):
    """Returned by session acquire / get."""

    session_id: str
    user_id: int
    client_type: str
    created_at: float


class SessionRenewResponse(BaseModel):
    renewed: bool


class RealtimeRequest(BaseModel):
    """Body for POST /cnc/realtime."""

    action: str  # pause | resume | stop | soft_reset


class GatewayStateResponse(BaseModel):
    """Returned by GET /cnc/gateway/state."""

    state: Optional[str] = None
    running: bool
