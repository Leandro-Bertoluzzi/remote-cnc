from celery import Celery
from pathlib import Path
from celery.utils.log import get_task_logger

###########################################################
#      Allow importing modules from parent directory      #
###########################################################

import sys
import os

# Get the current directory of the tasks.py file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (one level up)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to sys.path
sys.path.append(parent_dir)

###########################################################

try:
    from ..config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SERIAL_BAUDRATE, \
        SERIAL_PORT, FILES_FOLDER_PATH
    from ..database.models.task import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS
    from ..grbl.grblController import GrblController
    from ..utils.database import get_next_task, are_there_pending_tasks, \
        are_there_tasks_in_progress, update_task_status
except ImportError:
    from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SERIAL_BAUDRATE, \
        SERIAL_PORT, FILES_FOLDER_PATH
    from database.models.task import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS
    from grbl.grblController import GrblController
    from utils.database import get_next_task, are_there_pending_tasks, \
        are_there_tasks_in_progress, update_task_status

app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)


@app.task(name='worker.tasks.executeTask', bind=True)
def executeTask(self, admin_id: int) -> bool:
    # 1. Check if there is a task currently in progress, in which case return an exception
    if are_there_tasks_in_progress():
        raise Exception("There is a task currently in progress, please wait until finished")

    # 2. Instantiate a GrblController object and start communication with Arduino
    task_logger = get_task_logger(__name__)
    cnc = GrblController(logger=task_logger)
    cnc.connect(SERIAL_PORT, SERIAL_BAUDRATE)

    while are_there_pending_tasks():
        # 3. Get the file for the next task in the queue
        task = get_next_task()
        file_path = Path(f'../{FILES_FOLDER_PATH}/{task.file.user_id}/{task.file.file_path}')
        # Mark the task as 'in progress' in the DB
        update_task_status(task.id, TASK_IN_PROGRESS_STATUS, admin_id)
        task_logger.info('Started execution of file: %s', file_path)

        # Task progress
        progress = 0
        total_lines = 0

        # 4. Send G-code lines in a loop, until either the file is finished or there is an error
        with open(file_path, "r") as file:
            total_lines = len(file.readlines())

        with open(file_path, "r") as file:
            for line in file:
                cnc.streamLine(line)
                # update task progress
                progress = progress + 1
                percentage = int((progress * 100) / float(total_lines))
                status = cnc.queryStatusReport()
                parserstate = cnc.queryGcodeParserState()
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'percentage': percentage,
                        'progress': progress,
                        'total_lines': total_lines,
                        'status': status,
                        'parserstate': parserstate
                    }
                )

        # 5. When the file finishes, mark it as 'finished' in the DB and check
        # if there is a queued task in DB.
        # If there is none, close the connection and return
        task_logger.info('Finished execution of file: %s', file_path)
        update_task_status(task.id, TASK_FINISHED_STATUS, admin_id)
        # 6. If there is a pending task, go to step 3 and repeat

    cnc.disconnect()
    return True
