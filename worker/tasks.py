from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

app = Celery('worker',
             broker=os.environ['CELERY_BROKER_URL'],
             backend=os.environ['CELERY_RESULT_BACKEND'])

@app.task(name='worker.tasks.executeTask')
def executeTask() -> bool:
    # 1. Check if there is a task currently in progress, in which case return an exception
    # 2. Instantiate a SerialService object and start communication with Arduino
    # 3. Get the file for the next task in the queue
    # 4. Send G-code lines in a loop, until either the file is finished or there is an error
    # 5. When the file finishes, mark it as 'finished in the DB' and check if there is a queued task in DB. If there is none, close the connection and return
    # 6. If there is a pending task, go to step 3 and repeat
    return True
