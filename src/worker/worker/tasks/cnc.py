"""Celery task wrapper for CNC file execution.

This module is the **composition root** for the ``execute_task`` task:
it builds the concrete infrastructure adapters and delegates all application
logic to the pure handler in ``worker.tasks.handlers.cnc_handler``.

No business logic lives here — add it to the handler instead.
"""

from celery.utils.log import get_task_logger
from core.adapters.database.base import SessionLocal
from core.adapters.database.task_repository import TaskRepository
from core.adapters.file_storage import FileSystemStorage
from core.adapters.gateway.gateway_client import GatewayClient
from core.config import FILES_FOLDER_PATH
from worker.main import app
from worker.tasks.handlers.cnc_handler import execute_cnc_task


@app.task(name="execute_task", bind=True, ignore_result=True)
def executeTask(self, task_id: int) -> None:
    """Celery entry-point: build adapters and run the CNC execution handler.

    This wrapper is intentionally thin:
    - build concrete adapters
    - call ``execute_cnc_task`` with port-typed arguments
    - close the DB session in the finally block
    """
    db_session = SessionLocal()
    worker_logger = get_task_logger(__name__)

    try:
        execute_cnc_task(
            task_id=task_id,
            repo=TaskRepository(db_session),
            storage=FileSystemStorage(FILES_FOLDER_PATH),
            gateway=GatewayClient.from_config(),
            task_logger=worker_logger,
        )
    finally:
        db_session.close()
