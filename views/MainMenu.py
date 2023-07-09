from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from views.UsersView import UsersView
from views.TasksView import TasksView

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Ver estado de tareas'))
        layout.addWidget(MenuButton('Monitorizar equipo'))
        layout.addWidget(MenuButton('Administrar archivos'))
        layout.addWidget(MenuButton('Control manual y calibración'))
        layout.addWidget(MenuButton('Administrar tareas', goToView=TasksView, parent=self))
        layout.addWidget(MenuButton('Administrar usuarios', goToView=UsersView, parent=self))
        layout.addWidget(MenuButton('Administrar herramientas'))
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def redirectToView(self, view):
        self.parent().changeView(view)
