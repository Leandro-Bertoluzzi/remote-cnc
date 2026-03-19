"""FastAPI dependency for the Celery WorkerClient singleton."""

from typing import Annotated

from core.utilities.worker.workerClient import WorkerClient
from fastapi import Depends

_worker_client: WorkerClient | None = None


def get_worker_client() -> WorkerClient:
    """Return a shared WorkerClient instance (lazy-initialised)."""
    global _worker_client  # noqa: PLW0603
    if _worker_client is None:
        _worker_client = WorkerClient()
    return _worker_client


# Type alias for FastAPI dependency injection
GetWorker = Annotated[WorkerClient, Depends(get_worker_client)]
