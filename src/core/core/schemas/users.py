import re

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from core.database.types import RoleType

_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$"
)


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleType

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be 8-20 characters long with upper and lower case "
                "letters, numbers and special characters (@$!%*#?&)"
            )
        return v


class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    role: RoleType


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: RoleType
