from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.cards.RequestCard import RequestCard
from components.MenuButton import MenuButton
from database.models.task import TASK_PENDING_APPROVAL_STATUS
from database.repositories.taskRepository import getAllTasks

class RequestsView(QWidget):
    def __init__(self, parent=None):
        super(RequestsView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        tasks = getAllTasks(status=TASK_PENDING_APPROVAL_STATUS)
        for task in tasks:
            self.layout.addWidget(RequestCard(task, parent=self))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
