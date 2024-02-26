from PyQt5.QtWidgets import QPushButton, QMessageBox
from celery.result import AsyncResult
from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID, Globals, PROJECT_ROOT, SERIAL_BAUDRATE, SERIAL_PORT
from core.database.base import Session as SessionLocal
from core.database.models import Task, TASK_DEFAULT_PRIORITY, TASK_IN_PROGRESS_STATUS, \
    TASK_CANCELLED_STATUS, TASK_ON_HOLD_STATUS, TASK_REJECTED_STATUS, TASK_INITIAL_STATUS
from core.database.repositories.taskRepository import TaskRepository
from core.worker.tasks import executeTask


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
        description = f'Tarea {task.id}: {task.name}\nEstado: {task.status}'

        if task.status == TASK_IN_PROGRESS_STATUS:
            task_id = Globals.get_current_task_id()
            task_state = AsyncResult(task_id)

            task_info = task_state.info
            task_status = task_state.status

            if task_status == 'PROGRESS':
                description = 'Tarea {0}: {1}\nEstado: {2}\nProgreso: {3}/{4} ({5}%)'.format(
                    task.id,
                    task.name,
                    task.status,
                    task_info.get('progress'),
                    task_info.get('total_lines'),
                    task_info.get('percentage')
                )

            if task_status == 'FAILURE':
                description = f'Tarea {task.id}: {task.name}\nEstado: {task.status} (FAILED)'

        self.setDescription(description)

    def addButtons(self, status: str):
        """Adds buttons according to task status:

        * pending validation -> | Edit | Cancel |
        * on hold -> | Cancel | (Run) |
        * in progress -> No buttons
        * cancelled / rejected -> | Remove |
        * finished -> No buttons
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

        if status == TASK_ON_HOLD_STATUS and not self.device_busy:
            runTaskBtn = QPushButton("Ejecutar")
            runTaskBtn.clicked.connect(self.runTask)
            self.addButton(runTaskBtn)

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

    def removeTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar la tarea?')
        confirmation.setWindowTitle('Eliminar tarea')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() != QMessageBox.Yes:
            return

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

    def runTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Desea ejecutar la tarea ahora?')
        confirmation.setWindowTitle('Ejecutar tarea')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            if repository.are_there_tasks_in_progress():
                self.showError(
                    'Equipo ocupado',
                    'Ejecución cancelada: Ya hay una tarea en progreso'
                )
                return
            if confirmation.exec() != QMessageBox.Yes:
                return

            task = executeTask.delay(USER_ID, PROJECT_ROOT, SERIAL_PORT, SERIAL_BAUDRATE)
            Globals.set_current_task_id(task.task_id)
            QMessageBox.information(
                self,
                'Tarea enviada',
                'Se envió la tarea al equipo para su ejecución',
                QMessageBox.Ok
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.parent().refreshLayout()

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)
