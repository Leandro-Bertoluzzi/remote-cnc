from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']
)
