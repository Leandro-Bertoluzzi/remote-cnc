"""FastAPI dependency providing a ready-to-use ``LogManager`` instance."""

from typing import Annotated

from core.adapters.logging.log_storage import LogStorage
from core.application.log_manager import LogManager
from fastapi import Depends
from manager.adapters.api.middleware.dbMiddleware import GetFileRepository


def get_log_manager(repository: GetFileRepository) -> LogManager:
    """Build a ``LogManager`` with the request-scoped repository."""
    return LogManager(repository, LogStorage())


GetLogManager = Annotated[LogManager, Depends(get_log_manager)]
