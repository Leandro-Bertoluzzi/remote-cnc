"""FastAPI dependency for the WorkerClient singleton."""

from functools import lru_cache
from typing import Annotated

from core.adapters.worker.worker_client import WorkerClient
from core.ports.worker_client import IWorkerClient
from fastapi import Depends


@lru_cache(maxsize=1)
def get_worker_client() -> IWorkerClient:
    """Return a shared WorkerClient instance (created once, cached)."""
    return WorkerClient.from_config()


# Type alias for FastAPI dependency injection
GetWorker = Annotated[IWorkerClient, Depends(get_worker_client)]
