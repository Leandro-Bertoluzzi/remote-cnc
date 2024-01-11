from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.cards.MsgCard import MsgCard
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
from core.utils.database import get_all_tools, get_all_materials, \
    get_all_files_from_user, create_task, get_all_tasks_from_user


class TasksView(QWidget):
    def __init__(self, parent=None):
        super(TasksView, self).__init__(parent)

        try:
            self.files = [
                {'id': file.id, 'name': file.file_name} for file in get_all_files_from_user(USER_ID)
            ]
            self.materials = [
                {'id': material.id, 'name': material.name} for material in get_all_materials()
            ]
            self.tools = [
                {'id': tool.id, 'name': tool.name} for tool in get_all_tools()
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
                create_task(USER_ID, file_id, tool_id, material_id, name, note)
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
            tasks = get_all_tasks_from_user(USER_ID, status='all')
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.layout.addWidget(MenuButton('Crear tarea', onClick=self.createTask))

        for task in tasks:
            self.layout.addWidget(
                TaskCard(
                    task,
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
