from typing import Annotated

from core.domain.entities import User
from core.utilities.security import verify_token
from fastapi import Depends, HTTPException, Request
from jwt import ExpiredSignatureError, InvalidSignatureError
from manager.adapters.api.middleware.contextMiddleware import GetUserService


def auth_user(request: Request, user_service: GetUserService) -> User:
    token = None

    if "Authorization" in request.headers:
        token = request.headers["Authorization"].split(" ")[1]
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(401, detail="Unauthorized: Authentication Token is missing!")
    try:
        data = verify_token(token)
        user = user_service.get_user_by_id(data["user_id"])
    except ExpiredSignatureError as error:
        raise HTTPException(401, detail="Expired token, login to generate a new one") from error
    except InvalidSignatureError as error:
        raise HTTPException(401, detail="Invalid token, login to generate a new one") from error
    except Exception as error:
        raise HTTPException(400, detail=str(error)) from error

    return user


def auth_admin(request: Request, user_service: GetUserService) -> User:
    user = auth_user(request, user_service)

    if user.role != "admin":
        raise HTTPException(401, detail="Unauthorized: This endpoint requires admin permission")

    return user


# Type definitions

GetUserDep = Annotated[User, Depends(auth_user)]
GetAdminDep = Annotated[User, Depends(auth_admin)]
