"""FastAPI dependency for the shared WorkerClient."""

from typing import Annotated

from core.ports.worker_client import IWorkerClient
from fastapi import Depends
from manager.adapters.api.context import AppContext
from manager.adapters.api.middleware.contextMiddleware import get_app_context


def get_worker_client(context: Annotated[AppContext, Depends(get_app_context)]) -> IWorkerClient:
    return context.worker


# Type alias for FastAPI dependency injection
GetWorker = Annotated[IWorkerClient, Depends(get_worker_client)]
