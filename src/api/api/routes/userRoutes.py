from core.schemas.general import GenericResponse
from core.schemas.users import UserCreate, UserResponse, UserUpdate
from fastapi import APIRouter

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetUserRepository

userRoutes = APIRouter(prefix="/users", tags=["Users"])


@userRoutes.get("")
@userRoutes.get("/")
@userRoutes.get("/all")
def get_users(admin: GetAdminDep, repository: GetUserRepository) -> list[UserResponse]:
    users = repository.get_all_users()

    return [UserResponse.model_validate(user) for user in users]


@userRoutes.post("", response_model=UserResponse)
@userRoutes.post("/", response_model=UserResponse)
def create_new_user(request: UserCreate, admin: GetAdminDep, repository: GetUserRepository):
    return repository.create_user(request.name, request.email, request.password, request.role)


@userRoutes.put("/{user_id}", response_model=UserResponse)
def update_existing_user(
    user_id: int, request: UserUpdate, admin: GetAdminDep, repository: GetUserRepository
):
    result = repository.update_user(user_id, request.name, request.email, request.role)
    return UserResponse.model_validate(result)


@userRoutes.delete("/{user_id}", response_model=GenericResponse)
def remove_existing_user(user_id: int, admin: GetAdminDep, repository: GetUserRepository):
    repository.remove_user(user_id)
    return {"success": "El usuario fue eliminado con éxito"}


@userRoutes.get("/auth", response_model=UserResponse)
def authenticate(user: GetUserDep):
    return UserResponse.model_validate(user)
