from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from config import USER_ID
from database.repositories.taskRepository import updateTaskStatus, areThereTasksInProgress
from database.models.task import TASK_ON_HOLD_STATUS, TASK_REJECTED_STATUS
from utils.files import getFileNameInFolder
from worker.tasks import executeTask

class RequestCard(QWidget):
    def __init__(self, task, parent=None):
        super(RequestCard, self).__init__(parent)

        self.task = task

        taskDescription = QLabel(f'Tarea {task.id}: {task.name}')
        approveTaskBtn = QPushButton("Aprobar")
        approveTaskBtn.clicked.connect(self.approveTask)
        rejectTaskBtn = QPushButton("Rechazar")
        rejectTaskBtn.clicked.connect(self.rejectTask)

        layout = QHBoxLayout()
        layout.addWidget(taskDescription)
        layout.addWidget(approveTaskBtn)
        layout.addWidget(rejectTaskBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def approveTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea aprobar la solicitud?')
        confirmation.setWindowTitle('Aprobar solicitud')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            updateTaskStatus(self.task.id, TASK_ON_HOLD_STATUS, USER_ID)
            if not areThereTasksInProgress():
                executeTask.delay()
            self.parent().refreshLayout()

    def rejectTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea rechazar la solicitud?')
        confirmation.setWindowTitle('Rechazar solicitud')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            updateTaskStatus(self.task.id, TASK_REJECTED_STATUS, USER_ID)
            self.parent().refreshLayout()
