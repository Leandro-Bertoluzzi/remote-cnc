from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.cards.MsgCard import MsgCard
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.models import TASK_IN_PROGRESS_STATUS
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository


class TasksView(QWidget):
    def __init__(self, parent=None):
        super(TasksView, self).__init__(parent)

        db_session = SessionLocal()
        files_repository = FileRepository(db_session)
        materials_repository = MaterialRepository(db_session)
        tools_repository = ToolRepository(db_session)
        try:
            self.files = [
                {
                    'id': file.id,
                    'name': file.file_name
                } for file in files_repository.get_all_files_from_user(USER_ID)
            ]
            self.materials = [
                {
                    'id': material.id,
                    'name': material.name
                } for material in materials_repository.get_all_materials()
            ]
            self.tools = [
                {
                    'id': tool.id,
                    'name': tool.name
                } for tool in tools_repository.get_all_tools()
            ]
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials)
        if taskDialog.exec():
            file_id, tool_id, material_id, name, note = taskDialog.getInputs()
            try:
                db_session = SessionLocal()
                repository = TaskRepository(db_session)
                repository.create_task(USER_ID, file_id, tool_id, material_id, name, note)
            except Exception as error:
                self.showError(
                    'Error de base de datos',
                    str(error)
                )
                return
            self.refreshLayout()

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            tasks = repository.get_all_tasks_from_user(USER_ID, status='all')
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.layout.addWidget(MenuButton('Crear tarea', onClick=self.createTask))

        # Check if there is a task in progress
        device_running = any(TASK_IN_PROGRESS_STATUS in task.status for task in tasks)

        for task in tasks:
            self.layout.addWidget(
                TaskCard(
                    task,
                    device_running,
                    self.files,
                    self.tools,
                    self.materials,
                    parent=self
                )
            )

        if not tasks:
            self.layout.addWidget(MsgCard('La cola de tareas está vacía', self))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
