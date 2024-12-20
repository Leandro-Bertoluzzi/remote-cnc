from database.repositories.userRepository import UserRepository
from database.types import RoleType
from utilities.security import validate_password, generate_token
from fastapi import APIRouter, HTTPException
from api.middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel, EmailStr

rootRoutes = APIRouter()


# Health check
class HealthCheck(BaseModel):
    status: str = "OK"


@rootRoutes.get(
    "/health",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
    response_model=HealthCheck,
    response_description="Return HTTP Status Code 200 (OK)"
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


@rootRoutes.post(
    '/login',
    tags=["Login"],
    summary="User login",
    response_model=UserLoginResponse
)
def login(
    request: UserLogin,
    db_session: GetDbSession
):
    email = request.email
    password = request.password

    try:
        repository = UserRepository(db_session)
        user = repository.get_user_by_email(email)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    if not user:
        raise HTTPException(404, detail='No autorizado: Email inválido')

    checks = validate_password(user.password, password)
    if not checks:
        raise HTTPException(404, detail='No autorizado: Combinación inválida de email y contraseña')

    try:
        userData = user.__dict__
        userData['token'] = generate_token(user.id)
        return userData
    except Exception as error:
        raise HTTPException(400, detail=str(error))
