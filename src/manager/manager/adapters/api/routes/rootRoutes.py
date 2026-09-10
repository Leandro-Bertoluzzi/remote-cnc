from core.domain.types import RoleType
from core.utilities.security import generate_token, validate_password
from fastapi import APIRouter, HTTPException
from manager.adapters.api.middleware.contextMiddleware import GetUserService
from pydantic import BaseModel, EmailStr

rootRoutes = APIRouter()


# Health check
class HealthCheck(BaseModel):
    status: str = "OK"


@rootRoutes.get(
    "/health",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


# User login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleType
    token: str


@rootRoutes.post("/login", tags=["Login"], summary="User login", response_model=UserLoginResponse)
def login(request: UserLogin, user_service: GetUserService):
    user = user_service.get_user_by_email(request.email)

    if not user:
        raise HTTPException(404, detail="No autorizado: Email inválido")

    checks = validate_password(user.password, request.password)
    if not checks:
        raise HTTPException(404, detail="No autorizado: Combinación inválida de email y contraseña")

    if user.id is None:
        raise HTTPException(500, detail="User ID is required")

    return UserLoginResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        token=generate_token(user.id),
    )
