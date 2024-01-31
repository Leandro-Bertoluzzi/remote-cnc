from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.cards.MsgCard import MsgCard
from components.cards.RequestCard import RequestCard
from components.buttons.MenuButton import MenuButton
from core.database.base import Session as SessionLocal
from core.database.models import TASK_PENDING_APPROVAL_STATUS
from core.database.repositories.taskRepository import TaskRepository


class RequestsView(QWidget):
    def __init__(self, parent=None):
        super(RequestsView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

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
            tasks = repository.get_all_tasks(status=TASK_PENDING_APPROVAL_STATUS)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        for task in tasks:
            self.layout.addWidget(RequestCard(task, parent=self))

        if not tasks:
            self.layout.addWidget(MsgCard('No hay tareas pendientes de aprobación', self))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
