from core.database.repositories.userRepository import UserRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponseModel
from schemas.users import UserCreateModel, UserUpdateModel, UserResponse

userRoutes = APIRouter(prefix="/users", tags=["Users"])


@userRoutes.get('')
@userRoutes.get('/')
@userRoutes.get('/all')
def get_users(
    admin: GetAdminDep,
    db_session: GetDbSession
) -> list[UserResponse]:
    repository = UserRepository(db_session)
    users = repository.get_all_users()

    return [UserResponse.from_orm(user) for user in users]


@userRoutes.post('')
@userRoutes.post('/')
def create_new_user(
    request: UserCreateModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> UserResponse:
    name = request.name
    email = request.email
    password = request.password
    role = request.role

    try:
        repository = UserRepository(db_session)
        return repository.create_user(name, email, password, role)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@userRoutes.put('/{user_id}')
def update_existing_user(
    user_id: int,
    request: UserUpdateModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> UserResponse:
    name = request.name
    email = request.email
    role = request.role

    try:
        repository = UserRepository(db_session)
        result = repository.update_user(user_id, name, email, role)

        return UserResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@userRoutes.delete('/{user_id}')
def remove_existing_user(
    user_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> GenericResponseModel:
    try:
        repository = UserRepository(db_session)
        repository.remove_user(user_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'El usuario fue eliminado con éxito'}


@userRoutes.get('/auth')
def authenticate(user: GetUserDep) -> UserResponse:
    return UserResponse.from_orm(user)
