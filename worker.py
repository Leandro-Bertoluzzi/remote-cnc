from celery import Task
from celery.utils.log import get_task_logger
import time

try:
    from .cncworker.app import app
    from .database.base import Session as SessionLocal
    from .database.models import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS, \
        TASK_FAILED_STATUS
    from .database.repositories.taskRepository import TaskRepository
    from .grbl.grblController import GrblController
    from .utils.files import getFilePath
except ImportError:
    from cncworker.app import app
    from database.base import Session as SessionLocal
    from database.models import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS, \
        TASK_FAILED_STATUS
    from database.repositories.taskRepository import TaskRepository
    from grbl.grblController import GrblController
    from utils.files import getFilePath

# Constants
SEND_INTERVAL = 0.10    # Seconds
STATUS_POLL = 0.10      # Seconds
MAX_BUFFER_FILL = 75    # Percentage


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
    cnc.connect(serial_port, serial_baudrate)

    # Task progress
    sent_lines = 0
    processed_lines = 0
    total_lines = 0
    finished_sending = False
    # Initial CNC state
    status = cnc.getStatusReport()
    parserstate = cnc.getGcodeParserState()

    # Get the file lenght, while checking if it exists in the first place
    try:
        with open(file_path, 'r') as file:
            total_lines = len(file.readlines())
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
    gcode = open(file_path, 'r')

    while True:
        t = time.time()

        # Refresh machine position?
        if t - tp > STATUS_POLL:
            status = cnc.getStatusReport()
            parserstate = cnc.getGcodeParserState()
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

            # A 'program end' command was found (M2/M30)
            if cnc.finished():
                break

            if cnc.failed():
                break

            # GRBL finished executing file
            if processed_lines >= total_lines and finished_sending:
                break

            tp = t

        # Send new command?
        if t - ts > SEND_INTERVAL and not finished_sending:
            # Try not to fill the GRBL buffer
            if cnc.getBufferFill() > MAX_BUFFER_FILL:
                continue

            line = gcode.readline()

            # EOF
            if not line:
                gcode.close()
                finished_sending = True
                continue

            cnc.sendCommand(line)

            # update task progress
            sent_lines = sent_lines + 1
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

    if cnc.failed():
        task_logger.critical('Failed execution of file: %s', file_path)
        repository.update_task_status(task.id, TASK_FAILED_STATUS)

        if cnc.alarm():
            alarm_message = (
                f'An alarm was triggered (code: {cnc.alarm_code}) '
                f'while executing line: {cnc.error_line}'
            )
            task_logger.critical(alarm_message)
            raise Exception(alarm_message)

        error_message = f'There was an error when executing line: {cnc.error_line}'
        task_logger.critical(error_message)
        raise Exception(error_message)

    # SUCCESS
    task_logger.info('Finished execution of file: %s', file_path)
    repository.update_task_status(task.id, TASK_FINISHED_STATUS)

    return True
