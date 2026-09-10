"""Celery task wrapper for CNC file execution.

This module is the **composition root** for the ``execute_task`` task:
it builds the concrete infrastructure adapters and delegates all application
logic to the handler.

No business logic lives here — add it to the handler instead.
"""

import logging

from core.config import FILES_FOLDER_PATH
from infrastructure.database.base import SessionLocal
from infrastructure.database.task_repository import TaskRepository
from infrastructure.file_storage import FileSystemStorage
from infrastructure.gateway.gateway_client import GatewayClient
from infrastructure.logging.logger_factory import setup_task_logger
from worker.application.cnc_handler import execute_cnc_task
from worker.main import app


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
