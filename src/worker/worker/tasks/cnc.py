"""Celery tasks for CNC file execution.

The `execute_task` task orchestrates the execution of a G-code file through the CNC Gateway:

1. Validates the task in the DB and marks it as IN_PROGRESS.
2. Acquires a Gateway session and requests file execution.
3. Waits for file_finished / file_failed events via Redis PubSub.
4. Updates the task status in the DB accordingly.

The heavy lifting (serial I/O, line-by-line sending, pause/resume) is handled
entirely by the CNC Gateway process.
"""

import json
import logging

from celery.utils.log import get_task_logger
from core.config import FILES_FOLDER_PATH
from core.database.base import SessionLocal
from core.database.models import TaskStatus
from core.database.repositories.taskRepository import TaskRepository
from core.utilities.files import FileSystemHelper
from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
)
from core.utilities.gateway.gatewayClient import GatewayClient
from worker.main import app

logger = logging.getLogger(__name__)

# Timeout waiting for a file-execution event (seconds).
# A very long G-code file could run for hours, so we set a generous limit.
FILE_EVENT_TIMEOUT = 24 * 60 * 60  # 24 h


@app.task(name="execute_task", bind=True, ignore_result=True)
def executeTask(self, task_id: int) -> None:
    """Orchestrate a G-code file execution via the CNC Gateway.

    This task is purely a DB-orchestration wrapper:
    - it does NOT open a serial port
    - it does NOT send G-code lines itself
    - pause/resume/stop are handled by the Gateway's command queues

    The task blocks on Redis PubSub until the Gateway publishes a
    ``file_finished`` or ``file_failed`` event for the requested task.
    """
    db_session = SessionLocal()
    worker_logger = get_task_logger(__name__)
    gateway = GatewayClient()
    session_id: str | None = None
    pubsub = None

    try:
        repository = TaskRepository(db_session)

        # 1. Validate DB state
        if repository.are_there_tasks_in_progress():
            raise Exception("Ya hay una tarea en progreso, por favor espere a que termine")

        task = repository.get_task_by_id(task_id)
        if not task:
            raise Exception("No se encontró la tarea en la base de datos")

        if task.status != TaskStatus.APPROVED.value:
            raise Exception(f"La tarea tiene un estado incorrecto: {task.status}")

        # 2. Resolve the G-code file path
        files_helper = FileSystemHelper(FILES_FOLDER_PATH)
        file_path = files_helper.get_file_path(task.file.user_id, task.file.file_name)

        # 3. Acquire a Gateway session for the worker
        if not gateway.is_gateway_running():
            raise Exception("CNC Gateway no está disponible")

        session_id = gateway.acquire_session(
            user_id=task.user_id,
            client_type="worker",
        )
        if session_id is None:
            raise Exception("No se pudo adquirir la sesión: el CNC está en uso")

        # 4. Subscribe to events BEFORE requesting execution (no race)
        pubsub = gateway.subscribe_events()

        # 5. Mark the task as in-progress and request file execution
        repository.update_task_status(task.id, TaskStatus.IN_PROGRESS.value)
        worker_logger.info("Comenzada la ejecución del archivo: %s", file_path)

        gateway.request_file_execution(session_id, str(file_path), task.id)

        # 6. Wait for file_finished or file_failed
        _wait_for_completion(pubsub, task.id, worker_logger)

        # 7. Determine final status
        # If _wait_for_completion returned normally, the file finished successfully
        worker_logger.info("Finalizada la ejecución del archivo: %s", file_path)
        repository.update_task_status(task.id, TaskStatus.FINISHED.value)

    except _FileExecutionFailed as exc:
        # The Gateway reported a file_failed event
        worker_logger.critical("Error durante la ejecución: %s", exc.error)
        try:
            repository.update_task_status(task_id, TaskStatus.FAILED.value)
        except Exception:
            worker_logger.exception("No se pudo actualizar el estado de la tarea en la DB")
        raise Exception(exc.error) from exc

    finally:
        # Release session if we acquired one
        if session_id is not None:
            try:
                gateway.release_session(session_id)
            except Exception:
                worker_logger.warning("Error al liberar la sesión", exc_info=True)

        if pubsub is not None:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass

        db_session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FileExecutionFailed(Exception):
    """Internal signal: the Gateway reported a file_failed event."""

    def __init__(self, error: str):
        self.error = error
        super().__init__(error)


def _wait_for_completion(
    pubsub,
    task_id: int,
    task_logger,
) -> None:
    """Block on PubSub waiting for file_finished or file_failed.

    Progress monitoring is handled by consumers that subscribe directly
    to the ``grbl_status`` channel (Desktop, Web SSE). This function
    only cares about the terminal events.
    """
    import time

    deadline = time.time() + FILE_EVENT_TIMEOUT

    for raw_message in pubsub.listen():
        if time.time() > deadline:
            raise _FileExecutionFailed("Timeout esperando la finalización del archivo")

        if raw_message["type"] != "message":
            continue

        try:
            event = json.loads(raw_message["data"])
        except (json.JSONDecodeError, TypeError):
            continue

        event_type = event.get("type", "")
        event_task_id = event.get("task_id")

        # Only process events for *our* task
        if event_task_id is not None and event_task_id != task_id:
            continue

        if event_type == EVENT_FILE_FINISHED:
            task_logger.info(
                "Archivo finalizado: %d/%d líneas",
                event.get("sent_lines", 0),
                event.get("total_lines", 0),
            )
            return  # success

        elif event_type == EVENT_FILE_FAILED:
            raise _FileExecutionFailed(event.get("error", "Error desconocido"))
