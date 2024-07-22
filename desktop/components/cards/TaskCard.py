from celery.result import AsyncResult
from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from components.TaskProgress import TaskProgress
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.models import Task, TASK_DEFAULT_PRIORITY, TASK_FINISHED_STATUS, \
    TASK_CANCELLED_STATUS, TASK_ON_HOLD_STATUS, TASK_INITIAL_STATUS, \
    TASK_FAILED_STATUS, TASK_APPROVED_STATUS, TASK_IN_PROGRESS_STATUS
from core.database.repositories.taskRepository import TaskRepository
from core.utils.storage import get_value_from_id, get_value, set_value
from core.worker import WORKER_REQUEST_KEY, WORKER_PAUSE_REQUEST, WORKER_RESUME_REQUEST, \
    WORKER_IS_PAUSED_KEY
from helpers.cncWorkerMonitor import CncWorkerMonitor
from helpers.utils import needs_confirmation, send_task_to_worker
from PyQt5.QtWidgets import QSizePolicy, QPushButton


class TaskCard(Card):
    def __init__(
            self,
            task: Task,
            device_available: bool,
            files=[],
            tools=[],
            materials=[],
            parent=None
    ):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.device_available = device_available
        self.files = files
        self.tools = tools
        self.materials = materials
        self.setup_ui()

        # Set "status" dynamic property for styling
        self.setProperty("status", task.status)

    # UI MANAGEMENT

    def setup_ui(self):
        self.paused = False
        if self.task.status == TASK_IN_PROGRESS_STATUS:
            self.paused = not not get_value(WORKER_IS_PAUSED_KEY)

        self.setup_buttons(self.task.status)

        # Task description
        task_id = self.task.id
        task_name = self.task.name
        task_status_db = self.task.status
        self.setDescription(f'Tarea {task_id}: {task_name}\nEstado: {task_status_db}')

        # Check task status and update if necessary
        self.task_progress = TaskProgress()
        self.check_task_status()

    def check_task_status(self):
        # Check if it has a worker task ID
        task_worker_id = get_value_from_id('task', self.task.id)
        if not task_worker_id:
            return

        # Get status in worker
        task_state: AsyncResult = AsyncResult(task_worker_id)
        task_info = task_state.info
        task_status = task_state.status

        if task_status == 'PROGRESS' and self.task.status == TASK_IN_PROGRESS_STATUS:
            self.show_task_progress(task_info)

        if task_status == 'FAILURE':
            self.show_task_failure(task_info)

    def show_task_progress(self, task_info):
        sent_lines = task_info.get('sent_lines')
        processed_lines = task_info.get('processed_lines')
        total_lines = task_info.get('total_lines')

        # Progress bar
        self.task_progress.set_total(total_lines)
        self.task_progress.set_progress(sent_lines, processed_lines)

        # Update card layout
        self.task_progress.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.layout().addWidget(self.task_progress)

    def show_task_failure(self, task_info):
        error_msg = task_info
        description_error = (
            f'{self.label_description.text()}\n'
            f'Error: {error_msg}'
        )
        self.setDescription(description_error)

    def setup_buttons(self, status: str):
        """Adds buttons according to task status:

        * pending validation -> | Edit | Approve | Cancel |
        * on hold -> | Cancel | (Run) |
        * in progress -> | Pause/Resume |
        * cancelled -> | Remove | Restore |
        * finished -> | Repeat |
        * failed -> | Retry |
        """

        button_info = {
            TASK_INITIAL_STATUS: [
                ("Editar", self.updateTask),
                ("Aprobar", self.approveTask),
                ("Cancelar", self.cancelTask)
            ],
            TASK_ON_HOLD_STATUS: [("Cancelar", self.cancelTask)],
            TASK_CANCELLED_STATUS: [
                ("Eliminar", self.removeTask),
                ("Restaurar", self.restoreTask)
            ],
            TASK_IN_PROGRESS_STATUS: [
                ('Retomar' if self.paused else 'Pausar', self.pauseTask)
            ],
            TASK_FINISHED_STATUS: [("Repetir", self.repeatTask)],
            TASK_FAILED_STATUS: [("Reintentar", self.repeatTask)]
        }

        for status_value, data in button_info.items():
            if status == status_value:
                for (button_text, callback) in data:
                    self.addButton(button_text, callback)

        if status == TASK_ON_HOLD_STATUS:
            self.addButton("Ejecutar", self.runTask, self.device_available)

    # ACTIONS

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
        self.getView().refreshLayout()

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
        self.getView().refreshLayout()

    @needs_confirmation(
            '¿Realmente desea restaurar la tarea?'
            'Esto la devolverá al estado inicial, pendiente de aprobación',
            'Restaurar tarea'
    )
    def restoreTask(self):
        self.updateTaskStatus(TASK_INITIAL_STATUS)
        self.getView().refreshLayout()

    def cancelTask(self):
        cancelDialog = TaskCancelDialog()
        if not cancelDialog.exec():
            return

        cancellation_reason = cancelDialog.getInput()
        self.updateTaskStatus(TASK_CANCELLED_STATUS, cancellation_reason)
        self.getView().refreshLayout()

    def updateTaskStatus(
        self,
        new_status: str,
        cancellation_reason: str = ''
    ):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(
                self.task.id,
                new_status,
                USER_ID,
                cancellation_reason
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

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
        self.getView().refreshLayout()

    @needs_confirmation('¿Desea ejecutar la tarea ahora?', 'Ejecutar tarea')
    def runTask(self):
        if not CncWorkerMonitor.is_device_enabled():
            self.showError(
                'Equipo deshabilitado',
                'Ejecución cancelada: El equipo está deshabilitado'
            )
            return

        if CncWorkerMonitor.is_worker_running():
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
        self.getView().refreshLayout()

    @needs_confirmation('¿Realmente desea aprobar la solicitud?', 'Aprobar solicitud')
    def approveTask(self):
        self.updateTaskStatus(TASK_APPROVED_STATUS)
        self.getView().refreshLayout()

    def pauseTask(self):
        for i in range(self.layout_buttons.count()):
            widget = self.layout_buttons.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setText('Pausar' if self.paused else 'Retomar')

        if self.paused:
            set_value(WORKER_REQUEST_KEY, WORKER_RESUME_REQUEST)
        else:
            set_value(WORKER_REQUEST_KEY, WORKER_PAUSE_REQUEST)

        self.paused = not self.paused
