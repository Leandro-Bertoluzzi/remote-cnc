from celery import Celery
from config import USER_ID, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, FILES_FOLDER_PATH
from database.repositories.taskRepository import getNextTask, areTherePendingTasks, areThereTasksInProgress, updateTaskStatus

app = Celery(
    'worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@app.task(name='worker.tasks.executeTask')
def executeTask() -> bool:
    # 1. Check if there is a task currently in progress, in which case return an exception
    if areThereTasksInProgress():
        raise Exception("There is a task currently in progress, please wait until finished")

    # 2. Instantiate a SerialService object and start communication with Arduino
    # TO DO

    while areTherePendingTasks():
        # 3. Get the file for the next task in the queue
        task = getNextTask()
        file_path = f'{FILES_FOLDER_PATH}/{task.file.file_path}'

        # 4. Send G-code lines in a loop, until either the file is finished or there is an error
        with open(file_path, "r") as file:
            for line in file:
                print(line)

        # 5. When the file finishes, mark it as 'finished' in the DB and check if there is a queued task in DB. If there is none, close the connection and return
        updateTaskStatus(task.id, 'finished', USER_ID)
        # 6. If there is a pending task, go to step 3 and repeat

    return True
