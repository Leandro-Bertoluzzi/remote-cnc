from celery import Celery, Task
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)


# Constants
COMMANDS_CHANNEL = 'worker_commands'


# Definition of tasks

@app.task(name='execute_task', bind=True)
def executeTask(
    self: Task,
    task_id: int,
    serial_port: str,
    serial_baudrate: int
) -> bool:
    pass


@app.task(name='cnc_server', bind=True)
def cncServer(
    self: Task,
    serial_port: str,
    serial_baudrate: int
) -> bool:
    pass


@app.task(name='create_thumbnail')
def createThumbnail(file_id: int) -> bool:
    pass


@app.task(name='generate_report')
def generateFileReport(file_id: int) -> bool:
    pass
