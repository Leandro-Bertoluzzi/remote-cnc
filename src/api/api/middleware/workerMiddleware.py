"""FastAPI dependency for the WorkerClient singleton."""

from typing import Annotated

from core.adapters.worker.worker_client import WorkerClient
from core.ports.worker_client import IWorkerClient
from fastapi import Depends

_worker_client: IWorkerClient | None = None


def get_worker_client() -> IWorkerClient:
    """Return a shared WorkerClient instance (lazy-initialised)."""
    global _worker_client  # noqa: PLW0603
    if _worker_client is None:
        _worker_client = WorkerClient.from_config()
    return _worker_client


# Type alias for FastAPI dependency injection
GetWorker = Annotated[IWorkerClient, Depends(get_worker_client)]
