from PyQt5.QtWidgets import QPushButton, QMessageBox
from config import USER_ID
from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog, FROM_REJECT
from database.repositories.taskRepository import updateTaskStatus, areThereTasksInProgress
from database.models.task import TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
from worker.tasks import executeTask

class RequestCard(Card):
    def __init__(self, task, parent=None):
        super(RequestCard, self).__init__(parent)

        self.task = task

        description = f'Tarea {task.id}: {task.name}'
        approveTaskBtn = QPushButton("Aprobar")
        approveTaskBtn.clicked.connect(self.approveTask)
        rejectTaskBtn = QPushButton("Rechazar")
        rejectTaskBtn.clicked.connect(self.rejectTask)

        self.setDescription(description)
        self.addButton(approveTaskBtn)
        self.addButton(rejectTaskBtn)

    def approveTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea aprobar la solicitud?')
        confirmation.setWindowTitle('Aprobar solicitud')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            updateTaskStatus(self.task.id, TASK_APPROVED_STATUS, USER_ID)
            if not areThereTasksInProgress():
                executeTask.delay()
            self.parent().refreshLayout()

    def rejectTask(self):
        rejectDialog = TaskCancelDialog(origin=FROM_REJECT)
        if rejectDialog.exec():
            reject_reason = rejectDialog.getInput()
            updateTaskStatus(self.task.id, TASK_REJECTED_STATUS, USER_ID, reject_reason)
            self.parent().refreshLayout()
