"""Celery client for sending tasks to the worker without importing worker code.

Uses ``app.send_task()`` so the API / desktop can dispatch work to the broker
by task *name* only.
"""

from celery import Celery
from celery.result import AsyncResult

from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


# ---------------------------------------------------------------------------
# Task dispatchers – each returns an AsyncResult, same as .delay()
# ---------------------------------------------------------------------------


def execute_task(task_id: int) -> AsyncResult:
    """Send *execute_task* to the worker."""
    return app.send_task("execute_task", args=[task_id])


def create_thumbnail(file_id: int) -> AsyncResult:
    """Send *create_thumbnail* to the worker."""
    return app.send_task("create_thumbnail", args=[file_id])


def generate_file_report(file_id: int) -> AsyncResult:
    """Send *generate_report* to the worker."""
    return app.send_task("generate_report", args=[file_id])
