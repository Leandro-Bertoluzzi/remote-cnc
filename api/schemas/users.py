from core.database.types import RoleType
from pydantic import BaseModel, EmailStr, Field


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


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleType
