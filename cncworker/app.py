from celery import Celery
try:
    from ..config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
except ImportError:
    from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)
