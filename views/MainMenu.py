from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from components.buttons.MainMenuButton import MainMenuButton
from views.ControlView import ControlView
from views.FilesView import FilesView
from views.InventoryView import InventoryView
from views.RequestsView import RequestsView
from views.UsersView import UsersView
from views.TasksView import TasksView

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QGridLayout()
        layout.addWidget(MainMenuButton('Tareas\n', 'tasks.svg', TasksView, parent=self), 0, 0)
        layout.addWidget(MainMenuButton('Monitoreo\n', 'monitor.svg'), 0, 1)
        layout.addWidget(MainMenuButton('Archivos\n', 'files.svg', FilesView, parent=self), 0, 2)
        layout.addWidget(MainMenuButton('Control manual\ny calibración', 'control.svg', ControlView, parent=self), 0, 3)
        layout.addWidget(MainMenuButton('Solicitudes\n', 'requests.svg', RequestsView, parent=self), 1, 0)
        layout.addWidget(MainMenuButton('Usuarios\n', 'users.svg', UsersView, parent=self), 1, 1)
        layout.addWidget(MainMenuButton('Inventario\n', 'inventory.svg', InventoryView, parent=self), 1, 2)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def redirectToView(self, view):
        self.parent().changeView(view)
