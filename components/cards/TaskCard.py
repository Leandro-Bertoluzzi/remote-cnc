from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from components.text.TaskLabel import TaskLabel
from core.database.base import Session as SessionLocal
from core.database.models import Task, TASK_DEFAULT_PRIORITY, TASK_FINISHED_STATUS, \
    TASK_CANCELLED_STATUS, TASK_ON_HOLD_STATUS, TASK_REJECTED_STATUS, TASK_INITIAL_STATUS
from core.database.repositories.taskRepository import TaskRepository
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
        self.setup_ui()

        # Set "status" dynamic property for styling
        self.setProperty("status", task.status)

    def setup_ui(self):
        self.add_buttons(self.task.status)
        self.label_description = TaskLabel(self.task, self)

    def add_buttons(self, status: str):
        """Adds buttons according to task status:

        * pending validation -> | Edit | Cancel |
        * on hold -> | Cancel | (Run) |
        * in progress -> No buttons
        * cancelled / rejected -> | Remove | Restore |
        * finished -> | Repeat |
        """

        button_info = {
            TASK_INITIAL_STATUS: [
                ("Editar", self.updateTask),
                ("Cancelar", self.cancelTask)
            ],
            TASK_ON_HOLD_STATUS: [("Cancelar", self.cancelTask)],
            TASK_CANCELLED_STATUS: [
                ("Eliminar", self.removeTask),
                ("Restaurar", self.restoreTask)
            ],
            TASK_REJECTED_STATUS: [
                ("Eliminar", self.removeTask),
                ("Restaurar", self.restoreTask)
            ],
            TASK_FINISHED_STATUS: [("Repetir", self.repeatTask)]
        }

        for status_value, data in button_info.items():
            if status == status_value:
                for (button_text, callback) in data:
                    self.addButton(button_text, callback)

        if status == TASK_ON_HOLD_STATUS:
            self.addButton("Ejecutar", self.runTask, not self.device_busy)

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
        self.updateTaskStatus(
            self.task.id,
            TASK_INITIAL_STATUS
        )
        self.parent().refreshLayout()

    def cancelTask(self):
        cancelDialog = TaskCancelDialog()
        if not cancelDialog.exec():
            return

        cancellation_reason = cancelDialog.getInput()
        self.updateTaskStatus(
            self.task.id,
            TASK_CANCELLED_STATUS,
            cancellation_reason
        )
        self.parent().refreshLayout()

    def updateTaskStatus(
        self,
        task_id: int,
        new_status: str,
        cancellation_reason: str = ''
    ):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(
                task_id,
                new_status,
                None,
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
        self.parent().refreshLayout()

    @needs_confirmation('¿Desea ejecutar la tarea ahora?', 'Ejecutar tarea')
    def runTask(self):
        if not CncWorkerMonitor.is_device_enabled():
            self.showError(
                'Equipo deshabilitado',
                'Ejecución cancelada: El equipo está deshabilitado'
            )
            return

        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            if repository.are_there_tasks_in_progress():
                self.showError(
                    'Equipo ocupado',
                    'Ejecución cancelada: Ya hay una tarea en progreso'
                )
                return
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        worker_task_id = send_task_to_worker(self.task.id)
        self.getWindow().startWorkerMonitor(worker_task_id)
        self.showInformation(
            'Tarea enviada',
            'Se envió la tarea al equipo para su ejecución'
        )
        self.parent().refreshLayout()
