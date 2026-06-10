"""Celery task wrapper for CNC file execution.

This module is the **composition root** for the ``execute_task`` task:
it builds the concrete infrastructure adapters and delegates all application
logic to the pure handler in ``worker.tasks.handlers.cnc_handler``.

No business logic lives here — add it to the handler instead.
"""

import logging

from core.adapters.database.base import SessionLocal
from core.adapters.database.task_repository import TaskRepository
from core.adapters.file_storage import FileSystemStorage
from core.adapters.gateway.gateway_client import GatewayClient
from core.adapters.logging.logger_factory import setup_task_logger
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
    repo = TaskRepository(db_session)

    # Resolve the G-code filename for a meaningful per-task log file.
    # Falls back to the task ID if the record cannot be fetched.
    try:
        task_record = repo.get_task_by_id(task_id)
        log_name = task_record.file.file_name if task_record and task_record.file else str(task_id)
    except Exception:
        log_name = str(task_id)

    task_file_logger = setup_task_logger(log_name, logging.INFO)

    try:
        execute_cnc_task(
            task_id=task_id,
            repo=repo,
            storage=FileSystemStorage(FILES_FOLDER_PATH),
            gateway=GatewayClient.from_config(),
            task_logger=task_file_logger,
            task_logger_name=task_file_logger.name,
        )
    finally:
        db_session.close()
