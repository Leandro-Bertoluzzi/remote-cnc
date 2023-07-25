from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
from database.repositories.fileRepository import getAllFilesFromUser
from database.repositories.materialRepository import getAllMaterials
from database.repositories.taskRepository import createTask, getAllTasksFromUser, areThereTasksInProgress
from database.repositories.toolRepository import getAllTools
from worker.tasks import executeTask

class TasksView(QWidget):
    def __init__(self, parent=None):
        super(TasksView, self).__init__(parent)

        self.files = [{'id': file.id, 'name': file.file_name} for file in getAllFilesFromUser(USER_ID)]
        self.materials = [{'id': material.id, 'name': material.name} for material in getAllMaterials()]
        self.tools = [{'id': tool.id, 'name': tool.name} for tool in getAllTools()]

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials)
        if taskDialog.exec():
            file_id, tool_id, material_id, name, note = taskDialog.getInputs()
            createTask(USER_ID, file_id, tool_id, material_id, name, note)

            if not areThereTasksInProgress():
                executeTask.delay()
            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(MenuButton('Crear tarea', onClick=self.createTask))

        tasks = getAllTasksFromUser(USER_ID, status='all')
        for task in tasks:
            self.layout.addWidget(TaskCard(task, self.files, self.tools, self.materials, parent=self))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
