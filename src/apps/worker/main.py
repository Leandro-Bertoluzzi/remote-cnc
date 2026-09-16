from celery import Celery
from core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery(
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["apps.worker.tasks.cnc", "apps.worker.tasks.files"],
)
