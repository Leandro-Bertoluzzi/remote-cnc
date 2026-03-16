"""Global exception handlers for the FastAPI application.

Centralizes error handling so that route functions can focus on
business logic instead of repetitive try/except blocks.
"""

import logging

from core.database.exceptions import DatabaseError, EntityNotFoundError, Unauthorized
from core.database.repositories.fileRepository import (
    DuplicatedFileError,
    DuplicatedFileNameError,
)
from core.database.repositories.taskRepository import InvalidTaskStatus
from core.database.repositories.userRepository import DuplicatedUserError, InvalidRole
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(_request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(Unauthorized)
    async def unauthorized_handler(_request: Request, exc: Unauthorized) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(DatabaseError)
    async def database_error_handler(_request: Request, exc: DatabaseError) -> JSONResponse:
        logger.error("Database error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal database error"})

    @app.exception_handler(DuplicatedFileError)
    async def duplicated_file_handler(_request: Request, exc: DuplicatedFileError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DuplicatedFileNameError)
    async def duplicated_file_name_handler(
        _request: Request, exc: DuplicatedFileNameError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DuplicatedUserError)
    async def duplicated_user_handler(_request: Request, exc: DuplicatedUserError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InvalidRole)
    async def invalid_role_handler(_request: Request, exc: InvalidRole) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(InvalidTaskStatus)
    async def invalid_task_status_handler(
        _request: Request, exc: InvalidTaskStatus
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
