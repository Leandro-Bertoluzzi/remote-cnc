from core.database.repositories.userRepository import UserRepository
from core.database.types import RoleType
from core.utils.security import validate_password
from fastapi import APIRouter, status, HTTPException
from middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel, EmailStr
from services.security import generate_token

rootRoutes = APIRouter()

# Heakth check
class HealthCheck(BaseModel):
    status: str = "OK"


@rootRoutes.get(
    "/health",
    tags=["Healthcheck"],
    summary="Perform a Health Check",
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
class UserLoginModel(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponseModel(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleType
    token: str

@rootRoutes.post(
    '/login',
    tags=["Login"],
    summary="User login",
)
def login(
    request: UserLoginModel,
    db_session: GetDbSession
) -> UserLoginResponseModel:
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
        userData = user.serialize()
        userData['token'] = generate_token(user.id)
        return userData
    except Exception as error:
        raise HTTPException(400, detail=str(error))
