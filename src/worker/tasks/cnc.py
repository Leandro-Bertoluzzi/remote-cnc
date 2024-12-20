from celery import Task
from celery.utils.log import get_task_logger
import json
import time

from start_worker import app
from config import FILES_FOLDER_PATH
from database.base import SessionLocal
from database.models import TaskStatus
from database.repositories.taskRepository import TaskRepository
from utilities.gcode.gcodeFileSender import GcodeFileSender, FinishedFile
from utilities.grbl.grblController import GrblController
from utilities.files import FileSystemHelper
from utilities.loggerFactory import setup_task_logger, setup_stream_logger
from utilities.redisPubSubManager import RedisPubSubManagerSync
from utilities.worker.workerStatusManager import WorkerStatusManager

# Constants
SEND_INTERVAL = 0.10    # Seconds
STATUS_POLL = 0.10      # Seconds
STATUS_CHANNEL = 'grbl_status'
COMMANDS_CHANNEL = 'worker_commands'


@app.task(name='execute_task', bind=True, ignore_result=True)
def executeTask(
    self: Task,
    task_id: int,
    serial_port: str,
    serial_baudrate: int
) -> bool:
    db_session = SessionLocal()
    repository = TaskRepository(db_session)
    # 1. Check if there is a task currently in progress, in which case return an exception
    if repository.are_there_tasks_in_progress():
        raise Exception('Ya hay una tarea en progreso, por favor espere a que termine')

    # 2. Get the file for the requested task
    task = repository.get_task_by_id(task_id)
    if not task:
        raise Exception('No se encontró la tarea en la base de datos')

    if task.status != TaskStatus.APPROVED.value:
        raise Exception('La tarea tiene un estado incorrecto: {}'.format(task.status))

    files_helper = FileSystemHelper(FILES_FOLDER_PATH)
    file_path = files_helper.getFilePath(task.file.user_id, task.file.file_name)

    # 3. Instantiate a GrblController object and start communication with Arduino
    worker_logger = get_task_logger(__name__)
    task_logger = setup_task_logger(task.file.file_name, worker_logger.level)
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

    # 4. Initiate the file sender
    file_sender = GcodeFileSender(cnc, file_path)
    try:
        # Account for line added at the end (G4 P0)
        total_lines = file_sender.start() + 1
    except Exception as error:
        cnc.disconnect()
        worker_logger.critical('Error al abrir el archivo: {}'.format(file_path))
        worker_logger.critical(error)
        raise error

    # Once sure the file exists, mark the task as 'in progress' in the DB
    repository.update_task_status(task.id, TaskStatus.IN_PROGRESS.value)
    worker_logger.info('Comenzada la ejecución del archivo: {}'.format(file_path))

    # 5. Start a PubSub manager to notify updates and listen to requests
    redis = RedisPubSubManagerSync()
    redis.connect()

    # 6. Send G-code lines in a loop, until either the file is finished or there is an error
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
            message = json.dumps({
                'processed_lines': processed_lines,
                'total_lines': total_lines,
                'status': status,
                'parserstate': parserstate
            })
            redis.publish(STATUS_CHANNEL, message)

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
                cnc.sendCommand('G4 P0')    # Ask to wait for finish
                sent_lines += 1
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
            message = json.dumps({
                'sent_lines': sent_lines,
                'total_lines': total_lines
            })
            redis.publish(STATUS_CHANNEL, message)

            ts = t

    # 7. When the file finishes (or fails), disconnect from the GRBL device
    # and update its status in the DB

    cnc.disconnect()
    redis.disconnect()

    if cnc_status.failed():
        worker_logger.critical('Error durante la ejecución del archivo: {}'.format(file_path))
        repository.update_task_status(task.id, TaskStatus.FAILED.value)

        error_message = cnc_status.get_error_message()
        worker_logger.critical(error_message)
        raise Exception(error_message)

    # SUCCESS
    worker_logger.info('Finalizada la ejecución del archivo: {}'.format(file_path))
    repository.update_task_status(task.id, TaskStatus.FINISHED.value)


@app.task(name='cnc_server', bind=True, ignore_result=True)
def cncServer(
    self: Task,
    serial_port: str,
    serial_baudrate: int
) -> bool:
    db_session = SessionLocal()
    repository = TaskRepository(db_session)
    # 1. Check if there is a task currently in progress, in which case return an exception
    if repository.are_there_tasks_in_progress():
        raise Exception('Hay una tarea en progreso, por favor espere a que termine')

    # 2. Instantiate a GrblController object and start communication with Arduino
    worker_logger = get_task_logger(__name__)
    task_logger = setup_stream_logger('cnc_server', worker_logger.level)
    cnc = GrblController(logger=task_logger)
    cnc_status = cnc.grbl_status
    cnc.connect(serial_port, serial_baudrate)

    # Initial CNC state
    status = cnc_status.get_status_report()
    parserstate = cnc_status.get_parser_state()
    worker_status = WorkerStatusManager()

    # 3. Start a PubSub manager to notify updates and listen to requests
    redis = RedisPubSubManagerSync()
    redis.connect()
    redis.subscribe(COMMANDS_CHANNEL)

    # 4. Send G-code lines in a loop until the user requests the disconnection
    tp = time.time()  # last time a command was sent and info was queried
    worker_logger.info('**Iniciado servidor de comandos CNC**')

    while True:
        t = time.time()

        # Refresh machine position?
        if t - tp > STATUS_POLL:
            status = cnc_status.get_status_report()
            parserstate = cnc_status.get_parser_state()
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': status,
                    'parserstate': parserstate
                }
            )
            message = json.dumps({
                'status': status,
                'parserstate': parserstate
            })
            redis.publish(STATUS_CHANNEL, message)

            if cnc_status.finished():
                worker_logger.info('Encontrado comando de fin de programa, desconectando...')
                break

            # Check if PAUSE or RESUME was requested
            pause, resume = worker_status.process_request()

            if pause:
                cnc.setPaused(True)

            if resume:
                cnc.setPaused(False)

            if worker_status.is_paused():
                time.sleep(1)
                continue

            # Check if a command was requested
            received = redis.get_message()
            if received is not None and 'data' in received.keys():
                data: bytes = received['data']
                cnc.sendCommand(data.decode())

            tp = t

    # 5. When the user requests the disconnection (or a finish command is found),
    # disconnect from the GRBL device

    cnc.disconnect()

    message = json.dumps({
        'status': cnc_status.get_status_report()
    })
    redis.publish(STATUS_CHANNEL, message)

    redis.disconnect()
    worker_logger.info('**Finalizado servidor de comandos CNC**')
