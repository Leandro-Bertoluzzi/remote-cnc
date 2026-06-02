"""Pure application-layer handler for CNC file execution.

This module contains NO concrete infrastructure imports. All dependencies
are received as ports (``typing.Protocol``).
"""

import json
import time

from core.domain.gateway import EVENT_FILE_FAILED, EVENT_FILE_FINISHED
from core.domain.task import TaskStatus
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.logger import ILogger
from core.ports.task_repository import ITaskRepository

# Timeout waiting for a file-execution event (seconds).
# A very long G-code file could run for hours, so we set a generous limit.
FILE_EVENT_TIMEOUT = 24 * 60 * 60  # 24 h


def execute_cnc_task(
    task_id: int,
    repo: ITaskRepository,
    storage: IFileStorage,
    gateway: IGatewayClient,
    task_logger: ILogger,
) -> None:
    """Orchestrate a G-code file execution via the CNC Gateway.

    This handler is purely a DB-orchestration coordinator:
    - it does NOT open a serial port
    - it does NOT send G-code lines itself
    - pause/resume/stop are handled by the Gateway's command queues

    The handler blocks on Redis PubSub until the Gateway publishes a
    ``file_finished`` or ``file_failed`` event for the requested task.

    Args:
        task_id: ID of the task to execute.
        repo: Task repository port.
        storage: File storage port.
        gateway: Gateway client port.
        task_logger: Logger instance.
    """
    session_id: str | None = None
    pubsub = None

    try:
        # 1. Validate DB state
        if repo.are_there_tasks_in_progress():
            raise Exception("Ya hay una tarea en progreso, por favor espere a que termine")

        task = repo.get_task_by_id(task_id)
        if not task:
            raise Exception("No se encontró la tarea en la base de datos")

        if task.status != TaskStatus.APPROVED.value:
            raise Exception(f"La tarea tiene un estado incorrecto: {task.status}")

        # 2. Resolve the G-code file path
        if task.file is None:
            raise Exception("Task must have an associated file")
        file_path = storage.get_file_path(task.file.user_id, task.file.file_name)

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
        if task.id is None:
            raise Exception("Persisted task must have ID")
        repo.update_task_status(task.id, TaskStatus.IN_PROGRESS.value)
        task_logger.info("Comenzada la ejecución del archivo: %s", file_path)

        gateway.request_file_execution(session_id, str(file_path), task.id)

        # 6. Wait for file_finished or file_failed
        _wait_for_completion(pubsub, task.id, task_logger)

        # 7. Determine final status
        task_logger.info("Finalizada la ejecución del archivo: %s", file_path)
        repo.update_task_status(task.id, TaskStatus.FINISHED.value)

    except _FileExecutionFailed as exc:
        # The Gateway reported a file_failed event
        task_logger.critical("Error durante la ejecución: %s", exc.error)
        try:
            repo.update_task_status(task_id, TaskStatus.FAILED.value)
        except Exception:
            task_logger.exception("No se pudo actualizar el estado de la tarea en la DB")
        raise Exception(exc.error) from exc

    finally:
        # Release session if we acquired one
        if session_id is not None:
            try:
                gateway.release_session(session_id)
            except Exception:
                task_logger.warning("Error al liberar la sesión", exc_info=True)

        if pubsub is not None:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


class _FileExecutionFailed(Exception):
    """Internal signal: the Gateway reported a file_failed event."""

    def __init__(self, error: str):
        self.error = error
        super().__init__(error)


def _wait_for_completion(pubsub, task_id: int, task_logger: ILogger) -> None:
    """Block on PubSub waiting for file_finished or file_failed.

    Progress monitoring is handled by consumers that subscribe directly
    to the ``grbl_status`` channel (Desktop, Web SSE). This function
    only cares about the terminal events.
    """
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
