from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
from utils.database import get_all_tools, get_all_materials, get_all_files_from_user, create_task, get_all_tasks_from_user

class TasksView(QWidget):
    def __init__(self, parent=None):
        super(TasksView, self).__init__(parent)

        self.files = [{'id': file.id, 'name': file.file_name} for file in get_all_files_from_user(USER_ID)]
        self.materials = [{'id': material.id, 'name': material.name} for material in get_all_materials()]
        self.tools = [{'id': tool.id, 'name': tool.name} for tool in get_all_tools()]

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials)
        if taskDialog.exec():
            file_id, tool_id, material_id, name, note = taskDialog.getInputs()
            create_task(USER_ID, file_id, tool_id, material_id, name, note)
            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(MenuButton('Crear tarea', onClick=self.createTask))

        tasks = get_all_tasks_from_user(USER_ID, status='all')
        for task in tasks:
            self.layout.addWidget(TaskCard(task, self.files, self.tools, self.materials, parent=self))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
