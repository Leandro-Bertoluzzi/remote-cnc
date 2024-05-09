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
    from .utils.storage import delete_value, get_value, set_value
except ImportError:
    from cncworker.app import app
    from database.base import Session as SessionLocal
    from database.models import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS, \
        TASK_FAILED_STATUS
    from database.repositories.taskRepository import TaskRepository
    from grbl.grblController import GrblController
    from utils.files import getFilePath
    from utils.storage import delete_value, get_value, set_value

# Constants
SEND_INTERVAL = 0.10    # Seconds
STATUS_POLL = 0.10      # Seconds
MAX_BUFFER_FILL = 75    # Percentage
WORKER_REQUEST_KEY = 'worker_request'
WORKER_PAUSE_REQUEST = 'grbl_pause'
WORKER_RESUME_REQUEST = 'grbl_resume'
WORKER_IS_PAUSED_KEY = 'worker_paused'


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
    paused = False
    # Initial CNC state
    status = cnc_status.get_status_report()
    parserstate = cnc_status.get_parser_state()
    cnc_status.set_tool(task.tool_id)

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

            if cnc_status.failed():
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

            # Check if PAUSE or RESUME was requested
            request = get_value(WORKER_REQUEST_KEY)

            if request == WORKER_PAUSE_REQUEST:
                cnc.setPaused(True)
                delete_value(WORKER_REQUEST_KEY)
                set_value(WORKER_IS_PAUSED_KEY, 'True')
                paused = True
                continue

            if request == WORKER_RESUME_REQUEST:
                cnc.setPaused(False)
                delete_value(WORKER_REQUEST_KEY)
                delete_value(WORKER_IS_PAUSED_KEY)
                paused = False

            if paused:
                time.sleep(1)
                continue

            line = gcode.readline()

            # EOF or end programm command
            if not line or (line.strip() in ['M2', 'M02', 'M30']):
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
