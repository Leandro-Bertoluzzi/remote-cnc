from core.database.models import RoleType
from core.database.repositories.userRepository import UserRepository
from core.utils.security import validate_password
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel, EmailStr, Field
from services.security import generate_token
from services.utilities import serializeList

userRoutes = APIRouter(prefix="/users", tags=["Users"])


class UserCreateModel(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(
        regex=r'\b^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$\b',
        description='Password must be 8-20 characters long with upper and lower case \
            letters, numbers and special characters (@$!%*#?&)'
        )
    role: RoleType


class UserUpdateModel(BaseModel):
    name: str
    email: EmailStr
    role: RoleType


class UserLoginModel(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleType


@userRoutes.get('')
@userRoutes.get('/')
@userRoutes.get('/all')
def get_users(
    admin: GetAdminDep,
    db_session: GetDbSession
) -> list[UserResponse]:
    repository = UserRepository(db_session)
    users = serializeList(repository.get_all_users())
    return users


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
        user = repository.create_user(name, email, password, role)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return user


@userRoutes.put('/{user_id}')
def update_existing_user(
    user_id: int,
    request: UserUpdateModel,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    name = request.name
    email = request.email
    role = request.role

    try:
        repository = UserRepository(db_session)
        repository.update_user(user_id, name, email, role)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The user was successfully updated'}


@userRoutes.delete('/{user_id}')
def remove_existing_user(
    user_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    try:
        repository = UserRepository(db_session)
        repository.remove_user(user_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The user was successfully removed'}


@userRoutes.post('/login')
def login(
    request: UserLoginModel,
    db_session: GetDbSession
):
    email = request.email
    password = request.password

    # Get user from DB
    try:
        repository = UserRepository(db_session)
        user = repository.get_user_by_email(email)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    if not user:
        raise HTTPException(404, detail='Unauthorized: Invalid email')

    checks = validate_password(user.password, password)
    if not checks:
        raise HTTPException(404, detail='Unauthorized: Invalid combination of email and password')

    try:
        userData = user.serialize()
        # token should expire after 24 hrs
        userData['token'] = generate_token(user.id)
        return {
            'message': 'Successfully fetched auth token',
            'data': userData
        }
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@userRoutes.get('/auth')
def authenticate(user: GetUserDep):
    return {
        'message': 'Successfully authenticated',
        'data': user.serialize()
    }
