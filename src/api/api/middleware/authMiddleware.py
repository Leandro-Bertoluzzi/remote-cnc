from typing import Annotated

from core.database.models import User
from core.utilities.security import verify_token
from fastapi import Depends, HTTPException, Request
from jwt import ExpiredSignatureError, InvalidSignatureError

from api.middleware.dbMiddleware import GetUserRepository


def auth_user(request: Request, repository: GetUserRepository) -> User:
    token = None

    if "Authorization" in request.headers:
        token = request.headers["Authorization"].split(" ")[1]
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(401, detail="Unauthorized: Authentication Token is missing!")
    try:
        data = verify_token(token)
        user = repository.get_user_by_id(data["user_id"])
    except ExpiredSignatureError as error:
        raise HTTPException(401, detail="Expired token, login to generate a new one") from error
    except InvalidSignatureError as error:
        raise HTTPException(401, detail="Invalid token, login to generate a new one") from error
    except Exception as error:
        raise HTTPException(400, detail=str(error)) from error

    return user


def auth_admin(request: Request, repository: GetUserRepository) -> User:
    user = auth_user(request, repository)

    if user.role != "admin":
        raise HTTPException(401, detail="Unauthorized: This endpoint requires admin permission")

    return user


# Type definitions

GetUserDep = Annotated[User, Depends(auth_user)]
GetAdminDep = Annotated[User, Depends(auth_admin)]
