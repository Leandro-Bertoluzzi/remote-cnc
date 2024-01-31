from PyQt5.QtWidgets import QPushButton, QMessageBox
from celery.result import AsyncResult
from components.cards.Card import Card
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import Globals
from core.database.base import Session as SessionLocal
from core.database.models import TASK_DEFAULT_PRIORITY, TASK_IN_PROGRESS_STATUS
from core.database.repositories.taskRepository import TaskRepository


class TaskCard(Card):
    def __init__(self, task, files=[], tools=[], materials=[], parent=None):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.files = files
        self.tools = tools
        self.materials = materials

        # Set "status" dynamic property for styling
        self.setProperty("status", task.status)

        description = f'Tarea {task.id}: {task.name}\nEstado: {task.status}'
        editTaskBtn = QPushButton("Editar")
        editTaskBtn.clicked.connect(self.updateTask)
        removeTaskBtn = QPushButton("Borrar")
        removeTaskBtn.clicked.connect(self.removeTask)

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
        self.addButton(editTaskBtn)
        self.addButton(removeTaskBtn)

    def updateTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if taskDialog.exec():
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

        if confirmation.exec() == QMessageBox.Yes:
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

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)
