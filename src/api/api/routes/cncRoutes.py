from typing import Annotated

import core.utilities.grbl.grblUtils as grblUtils
from core.schemas.cnc import CncCommand, CncJogCommand, CncJogResponse
from core.schemas.general import GenericResponse
from core.schemas.session import (
    GatewayStateResponse,
    RealtimeRequest,
    SessionAcquireRequest,
    SessionRenewResponse,
    SessionResponse,
)
from core.utilities.gateway.constants import (
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_SOFT_RESET,
    ACTION_STOP,
)
from core.utilities.serial import SerialService
from fastapi import APIRouter, Header, HTTPException

from api.middleware.authMiddleware import GetAdminDep
from api.middleware.gatewayMiddleware import GetGateway

cncRoutes = APIRouter(prefix="/cnc", tags=["CNC"])

# Header dependency for authenticated session commands
GetSessionId = Annotated[str, Header(description="Active CNC session ID")]


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------


@cncRoutes.get("/ports")
def get_available_ports(admin: GetAdminDep):
    available_ports = SerialService.get_ports()
    return {"ports": available_ports}


# ---------------------------------------------------------------------------
# Gateway state (read-only, no session required)
# ---------------------------------------------------------------------------


@cncRoutes.get("/gateway/state", response_model=GatewayStateResponse)
def get_gateway_state(admin: GetAdminDep, gateway: GetGateway):
    """Return the current CNC Gateway state."""
    state = gateway.get_gateway_state()
    return {"state": state, "running": state is not None}


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


@cncRoutes.post("/session", response_model=SessionResponse)
def acquire_session(
    admin: GetAdminDep,
    gateway: GetGateway,
    request: SessionAcquireRequest,
):
    """Acquire the exclusive CNC session (distributed lock)."""
    if not gateway.is_gateway_running():
        raise HTTPException(503, detail="CNC Gateway no está disponible")

    session_id = gateway.acquire_session(
        user_id=admin.id,
        client_type=request.client_type,
    )
    if session_id is None:
        raise HTTPException(409, detail="El CNC ya está en uso por otra sesión")

    session_data = gateway.get_active_session()
    return session_data


@cncRoutes.get("/session", response_model=SessionResponse)
def get_session(admin: GetAdminDep, gateway: GetGateway):
    """Get the current active session, if any."""
    session = gateway.get_active_session()
    if session is None:
        raise HTTPException(404, detail="No hay sesión activa")
    return session


@cncRoutes.put("/session/renew", response_model=SessionRenewResponse)
def renew_session(
    admin: GetAdminDep,
    gateway: GetGateway,
    x_cnc_session: GetSessionId,
):
    """Heartbeat — renew the session TTL."""
    renewed = gateway.renew_session(x_cnc_session)
    if not renewed:
        raise HTTPException(404, detail="Sesión no encontrada o expirada")
    return {"renewed": True}


@cncRoutes.delete("/session", response_model=GenericResponse)
def release_session(
    admin: GetAdminDep,
    gateway: GetGateway,
    x_cnc_session: GetSessionId,
):
    """Release the CNC session."""
    released = gateway.release_session(x_cnc_session)
    if not released:
        raise HTTPException(404, detail="Sesión no encontrada o no le pertenece")
    return {"success": "Sesión liberada correctamente"}


# ---------------------------------------------------------------------------
# Commands (require active session via X-CNC-Session header)
# ---------------------------------------------------------------------------


@cncRoutes.post("/command", response_model=GenericResponse)
def send_command(
    admin: GetAdminDep,
    gateway: GetGateway,
    request: CncCommand,
    x_cnc_session: GetSessionId,
):
    """Send a G-code command to the CNC via the Gateway."""
    if not gateway.is_gateway_running():
        raise HTTPException(503, detail="CNC Gateway no está disponible")

    gateway.send_command(x_cnc_session, request.command)
    return {"success": "El comando fue enviado para su ejecución"}


@cncRoutes.post("/jog", response_model=CncJogResponse)
def send_jog_command(
    admin: GetAdminDep,
    gateway: GetGateway,
    request: CncJogCommand,
    x_cnc_session: GetSessionId,
    machine: bool = False,
):
    """Send a jog command to the CNC via the Gateway."""
    if not gateway.is_gateway_running():
        raise HTTPException(503, detail="CNC Gateway no está disponible")

    gateway.send_jog(
        x_cnc_session,
        request.x,
        request.y,
        request.z,
        request.feedrate,
        units=request.units,
        distance_mode=request.mode,
        machine_coordinates=machine,
    )

    # Build locally just for the response
    code = grblUtils.build_jog_command(
        request.x,
        request.y,
        request.z,
        request.feedrate,
        units=request.units,
        distance_mode=request.mode,
        machine_coordinates=machine,
    )
    return {"command": code}


@cncRoutes.post("/realtime", response_model=GenericResponse)
def send_realtime_command(
    admin: GetAdminDep,
    gateway: GetGateway,
    request: RealtimeRequest,
    x_cnc_session: GetSessionId,
):
    """Send a realtime action (pause / resume / stop / soft_reset) to the CNC."""
    valid_actions = {ACTION_PAUSE, ACTION_RESUME, ACTION_STOP, ACTION_SOFT_RESET}
    if request.action not in valid_actions:
        raise HTTPException(
            400,
            detail=f"Acción inválida: {request.action}. "
            f"Opciones: {', '.join(sorted(valid_actions))}",
        )

    if not gateway.is_gateway_running():
        raise HTTPException(503, detail="CNC Gateway no está disponible")

    gateway.send_realtime(x_cnc_session, request.action)
    return {"success": f"Acción '{request.action}' enviada correctamente"}
