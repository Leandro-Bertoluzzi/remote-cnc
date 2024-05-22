from celery import Task
from celery.utils.log import get_task_logger
import time

try:
    from .cncworker.app import app
    from .cncworker.workerStatusManager import WorkerStatusManager
    from .database.base import Session as SessionLocal
    from .database.models import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS, \
        TASK_FAILED_STATUS
    from .database.repositories.taskRepository import TaskRepository
    from .gcode.gcodeFileSender import GcodeFileSender, FinishedFile
    from .grbl.grblController import GrblController
    from .utils.files import getFilePath
except ImportError:
    from cncworker.app import app
    from cncworker.workerStatusManager import WorkerStatusManager
    from database.base import Session as SessionLocal
    from database.models import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS, \
        TASK_FAILED_STATUS
    from database.repositories.taskRepository import TaskRepository
    from gcode.gcodeFileSender import GcodeFileSender, FinishedFile
    from grbl.grblController import GrblController
    from utils.files import getFilePath

# Constants
SEND_INTERVAL = 0.10    # Seconds
STATUS_POLL = 0.10      # Seconds


@app.task(name='worker.tasks.executeTask', bind=True)
def executeTask(
    self: Task,
    task_id: int,
    base_path: str,
    serial_port: str,
    serial_baudrate: int
) -> bool:
    db_session = SessionLocal()
    repository = TaskRepository(db_session)
    # 1. Check if there is a task currently in progress, in which case return an exception
    if repository.are_there_tasks_in_progress():
        raise Exception('There is a task currently in progress, please wait until finished')

    # 2. Get the file for the requested task
    task = repository.get_task_by_id(task_id)
    if not task:
        raise Exception('There are no pending tasks to process')

    file_path = getFilePath(base_path, task.file.user_id, task.file.file_name)

    # 3. Instantiate a GrblController object and start communication with Arduino
    task_logger = get_task_logger(__name__)
    cnc = GrblController(logger=task_logger)
    cnc_status = cnc.grbl_status
    cnc.connect(serial_port, serial_baudrate)

    # Task progress
    sent_lines = 0
    processed_lines = 0
    total_lines = 0
    finished_sending = False
    worker_status = WorkerStatusManager()
    # Initial CNC state
    status = cnc_status.get_status_report()
    parserstate = cnc_status.get_parser_state()
    cnc_status.set_tool(task.tool_id)

    # Initiates the file sender
    file_sender = GcodeFileSender(cnc, file_path)
    try:
        total_lines = file_sender.start()
    except Exception as error:
        cnc.disconnect()
        task_logger.critical('Error opening file: %s', file_path)
        task_logger.critical(error)
        repository.update_task_status(task.id, TASK_FAILED_STATUS)
        raise error

    # Once sure the file exists, mark the task as 'in progress' in the DB
    repository.update_task_status(task.id, TASK_IN_PROGRESS_STATUS)
    task_logger.info('Started execution of file: %s', file_path)

    # 4. Send G-code lines in a loop, until either the file is finished or there is an error
    ts = tp = time.time()  # last time a command was sent and info was queried

    while True:
        t = time.time()

        # Refresh machine position?
        if t - tp > STATUS_POLL:
            status = cnc_status.get_status_report()
            parserstate = cnc_status.get_parser_state()
            processed_lines = cnc.getCommandsCount()
            self.update_state(
                state='PROGRESS',
                meta={
                    'sent_lines': sent_lines,
                    'processed_lines': processed_lines,
                    'total_lines': total_lines,
                    'status': status,
                    'parserstate': parserstate
                }
            )

            if cnc_status.finished():
                break

            if cnc_status.failed():
                break

            # GRBL finished executing file
            if processed_lines >= total_lines and finished_sending:
                break

            tp = t

        # Send new command?
        if t - ts > SEND_INTERVAL and not finished_sending:
            # Check if PAUSE or RESUME was requested
            pause, resume = worker_status.process_request()

            if pause:
                cnc.setPaused(True)
                file_sender.pause()

            if resume:
                cnc.setPaused(False)
                file_sender.resume()

            if worker_status.is_paused():
                time.sleep(1)
                continue

            try:
                sent_lines = file_sender.send_line()
            except FinishedFile:
                finished_sending = True
                file_sender.stop()

            # update task progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'sent_lines': sent_lines,
                    'processed_lines': processed_lines,
                    'total_lines': total_lines,
                    'status': status,
                    'parserstate': parserstate
                }
            )

            ts = t

    # 5. When the file finishes (or fails), disconnect from the GRBL device
    # and update its status in the DB

    cnc.disconnect()

    if cnc_status.failed():
        task_logger.critical('Failed execution of file: %s', file_path)
        repository.update_task_status(task.id, TASK_FAILED_STATUS)

        error_message = cnc_status.get_error_message()
        task_logger.critical(error_message)
        raise Exception(error_message)

    # SUCCESS
    task_logger.info('Finished execution of file: %s', file_path)
    repository.update_task_status(task.id, TASK_FINISHED_STATUS)

    return True
