from PyQt5.QtWidgets import QPushButton
from celery.result import AsyncResult
from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.base import Session as SessionLocal
from core.database.models import Task, TASK_DEFAULT_PRIORITY, TASK_FINISHED_STATUS, \
    TASK_CANCELLED_STATUS, TASK_ON_HOLD_STATUS, TASK_REJECTED_STATUS, TASK_INITIAL_STATUS
from core.database.repositories.taskRepository import TaskRepository
from core.utils.storage import get_value_from_id
from helpers.cncWorkerMonitor import CncWorkerMonitor
from helpers.utils import needs_confirmation, send_task_to_worker


class TaskCard(Card):
    def __init__(
            self,
            task: Task,
            device_busy: bool,
            files=[],
            tools=[],
            materials=[],
            parent=None
    ):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.device_busy = device_busy
        self.files = files
        self.tools = tools
        self.materials = materials

        # Set "status" dynamic property for styling
        self.setProperty("status", task.status)

        # Populate card
        self.addButtons(task.status)
        self.set_task_description()

    def addButtons(self, status: str):
        """Adds buttons according to task status:

        * pending validation -> | Edit | Cancel |
        * on hold -> | Cancel | (Run) |
        * in progress -> No buttons
        * cancelled / rejected -> | Remove | Restore |
        * finished -> | Repeat |
        """
        if status == TASK_INITIAL_STATUS:
            editTaskBtn = QPushButton("Editar")
            editTaskBtn.clicked.connect(self.updateTask)
            self.addButton(editTaskBtn)

        if status == TASK_INITIAL_STATUS or status == TASK_ON_HOLD_STATUS:
            cancelTaskBtn = QPushButton("Cancelar")
            cancelTaskBtn.clicked.connect(self.cancelTask)
            self.addButton(cancelTaskBtn)

        if status == TASK_CANCELLED_STATUS or status == TASK_REJECTED_STATUS:
            removeTaskBtn = QPushButton("Eliminar")
            removeTaskBtn.clicked.connect(self.removeTask)
            self.addButton(removeTaskBtn)
            restoreTaskBtn = QPushButton("Restaurar")
            restoreTaskBtn.clicked.connect(self.restoreTask)
            self.addButton(restoreTaskBtn)

        if status == TASK_ON_HOLD_STATUS:
            runTaskBtn = QPushButton("Ejecutar")
            runTaskBtn.clicked.connect(self.runTask)
            runTaskBtn.setDisabled(self.device_busy)
            self.addButton(runTaskBtn)

        if status == TASK_FINISHED_STATUS:
            repeatTaskBtn = QPushButton("Repetir")
            repeatTaskBtn.clicked.connect(self.repeatTask)
            self.addButton(repeatTaskBtn)

    def set_task_description(self):
        # Default
        task_id = self.task.id
        task_name = self.task.name
        task_status_db = self.task.status
        description = f'Tarea {task_id}: {task_name}\nEstado: {task_status_db}'

        # Check if it has a worker task ID
        task_worker_id = get_value_from_id('task', self.task.id)
        if not task_worker_id:
            self.setDescription(description)
            return

        # Get status in worker
        task_state = AsyncResult(task_worker_id)
        task_info = task_state.info
        task_status = task_state.status

        if task_status == 'PROGRESS':
            sent_lines = task_info.get('sent_lines')
            processed_lines = task_info.get('processed_lines')
            total_lines = task_info.get('total_lines')

            sent = int((sent_lines * 100) / float(total_lines))
            executed = int((processed_lines * 100) / float(total_lines))

            description = (
                f'Tarea {task_id}: {task_name}\n'
                f'Estado: {task_status_db}\n'
                f'Enviado: {sent_lines}/{total_lines} ({sent}%)\n'
                f'Ejecutado: {processed_lines}/{total_lines} ({executed}%)'
            )

        if task_status == 'FAILURE':
            error_msg = task_info
            description = (
                f'Tarea {task_id}: {task_name}\nEstado: {task_status_db} (FAILED)\n'
                f'Error: {error_msg}'
            )

        self.setDescription(description)

    def updateTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task(
                self.task.id,
                self.task.user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note,
                TASK_DEFAULT_PRIORITY
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar la tarea?', 'Eliminar tarea')
    def removeTask(self):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.remove_task(self.task.id)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    @needs_confirmation(
            '¿Realmente desea restaurar la tarea?'
            'Esto la devolverá al estado inicial, pendiente de aprobación',
            'Restaurar tarea'
    )
    def restoreTask(self):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(
                self.task.id,
                TASK_INITIAL_STATUS
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    def cancelTask(self):
        cancelDialog = TaskCancelDialog()
        if not cancelDialog.exec():
            return

        cancellation_reason = cancelDialog.getInput()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(
                self.task.id,
                TASK_CANCELLED_STATUS,
                None,
                cancellation_reason
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    def repeatTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.create_task(
                self.task.user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    @needs_confirmation('¿Desea ejecutar la tarea ahora?', 'Ejecutar tarea')
    def runTask(self):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            if not CncWorkerMonitor.is_device_enabled():
                self.showError(
                    'Equipo deshabilitado',
                    'Ejecución cancelada: El equipo está deshabilitado'
                )
                return

            if repository.are_there_tasks_in_progress():
                self.showError(
                    'Equipo ocupado',
                    'Ejecución cancelada: Ya hay una tarea en progreso'
                )
                return

            worker_task_id = send_task_to_worker(self.task.id)
            self.getWindow().startWorkerMonitor(worker_task_id)
            self.showInformation(
                'Tarea enviada',
                'Se envió la tarea al equipo para su ejecución'
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()
