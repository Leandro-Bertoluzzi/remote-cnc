from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from worker.tasks import addTask

class TasksView(QWidget):
    def __init__(self, parent=None):
        super(TasksView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createTask(self):
        addTask.delay(1)

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(MenuButton('Crear tarea', onClick=self.createTask))

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.parent().backToMenu))
        self.update()
