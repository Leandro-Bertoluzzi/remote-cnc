###########################################################
###### Allow importing modules from parent directory ######
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

from celery import Celery
from config import USER_ID, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SERIAL_BAUDRATE, SERIAL_PORT, FILES_FOLDER_PATH
from database.models.task import TASK_FINISHED_STATUS, TASK_IN_PROGRESS_STATUS
from grbl.grblController import GrblController
from utils.database import get_next_task, are_there_pending_tasks, are_there_tasks_in_progress, update_task_status

app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@app.task(name='worker.tasks.executeTask', bind=True)
def executeTask(self) -> bool:
    # 1. Check if there is a task currently in progress, in which case return an exception
    if are_there_tasks_in_progress():
        raise Exception("There is a task currently in progress, please wait until finished")

    # 2. Instantiate a GrblController object and start communication with Arduino
    cnc = GrblController()
    cnc.connect(SERIAL_PORT, SERIAL_BAUDRATE)

    # Task progress
    progress: int = 0
    total_lines: int = 0

    while are_there_pending_tasks():
        # 3. Get the file for the next task in the queue
        task = get_next_task()
        file_path = f'../{FILES_FOLDER_PATH}/{task.file.file_path}'
        # Mark the task as 'in progress' in the DB
        update_task_status(task.id, TASK_IN_PROGRESS_STATUS, USER_ID)

        # 4. Send G-code lines in a loop, until either the file is finished or there is an error
        with open(file_path, "r") as file:
            total_lines = len(file.readlines())

        with open(file_path, "r") as file:
            for line in file:
                cnc.streamLine(line)
                # update task progress
                progress = progress + 1
                percentage = int((progress * 100) / float(total_lines))
                position = cnc.getMachinePosition()
                modal = cnc.getModalGroup()
                parameters = cnc.getParameters()
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': percentage,
                        'lines': progress,
                        'position': position,
                        'modal': modal,
                        'parameters': parameters
                    }
                )

        # 5. When the file finishes, mark it as 'finished' in the DB and check if there is a queued task in DB. If there is none, close the connection and return
        update_task_status(task.id, TASK_FINISHED_STATUS, USER_ID)
        # 6. If there is a pending task, go to step 3 and repeat

    cnc.disconnect()
    return True
