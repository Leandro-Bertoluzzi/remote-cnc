from PyQt5.QtWidgets import QPushButton, QMessageBox
from components.cards.Card import Card
from components.dialogs.TaskDataDialog import TaskDataDialog
from database.repositories.taskRepository import updateTask, removeTask
from database.models.task import TASK_DEFAULT_PRIORITY

class TaskCard(Card):
    def __init__(self, task, files=[], tools=[], materials=[], parent=None):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.files = files
        self.tools = tools
        self.materials = materials

        description = f'Tarea {task.id}: {task.name}\nEstado: {task.status}'
        editTaskBtn = QPushButton("Editar")
        editTaskBtn.clicked.connect(self.updateTask)
        removeTaskBtn = QPushButton("Borrar")
        removeTaskBtn.clicked.connect(self.removeTask)

        self.setDescription(description)
        self.addButton(editTaskBtn)
        self.addButton(removeTaskBtn)

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
