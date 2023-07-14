from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.dialogs.TaskDataDialog import TaskDataDialog
from database.repositories.taskRepository import updateTask, removeTask
from database.models.task import TASK_DEFAULT_PRIORITY

class TaskCard(QWidget):
    def __init__(self, task, files=[], tools=[], materials=[], parent=None):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.files = files
        self.tools = tools
        self.materials = materials

        taskDescription = QLabel(f'Tarea {task.id}: {task.name}')
        editTaskBtn = QPushButton("Editar")
        editTaskBtn.clicked.connect(self.updateTask)
        removeTaskBtn = QPushButton("Borrar")
        removeTaskBtn.clicked.connect(self.removeTask)

        layout = QHBoxLayout()
        layout.addWidget(taskDescription)
        layout.addWidget(editTaskBtn)
        layout.addWidget(removeTaskBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def updateTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if taskDialog.exec():
            file_id, tool_id, material_id, name, note = taskDialog.getInputs()
            updateTask(
                self.task.id,
                self.task.user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note,
                TASK_DEFAULT_PRIORITY
            )
            self.parent().refreshLayout()

    def removeTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar la tarea?')
        confirmation.setWindowTitle('Eliminar tarea')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            removeTask(self.task.id)
            self.parent().refreshLayout()
