"""Celery client for sending tasks to the worker without importing worker code.

Uses ``app.send_task()`` so the API / desktop can dispatch work to the broker
by task *name* only.
"""

from celery import Celery
from celery.result import AsyncResult

from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# Constants
COMMANDS_CHANNEL = "worker_commands"


# ---------------------------------------------------------------------------
# Task dispatchers – each returns an AsyncResult, same as .delay()
# ---------------------------------------------------------------------------


def execute_task(task_id: int, serial_port: str, serial_baudrate: int) -> AsyncResult:
    """Send *execute_task* to the worker."""
    return app.send_task("execute_task", args=[task_id, serial_port, serial_baudrate])


def cnc_server(serial_port: str, serial_baudrate: int) -> AsyncResult:
    """Send *cnc_server* to the worker."""
    return app.send_task("cnc_server", args=[serial_port, serial_baudrate])


def create_thumbnail(file_id: int) -> AsyncResult:
    """Send *create_thumbnail* to the worker."""
    return app.send_task("create_thumbnail", args=[file_id])


def generate_file_report(file_id: int) -> AsyncResult:
    """Send *generate_report* to the worker."""
    return app.send_task("generate_report", args=[file_id])
