from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from components.buttons.MainMenuButton import MainMenuButton
from views.ControlView import ControlView
from views.FilesView import FilesView
from views.InventoryView import InventoryView
from views.MonitorView import MonitorView
from views.RequestsView import RequestsView
from views.UsersView import UsersView
from views.TasksView import TasksView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class MainMenu(QWidget):
    def __init__(self, parent: 'MainWindow'):
        super(MainMenu, self).__init__(parent)

        # Buttons
        btn_tasks = self.createButton('Tareas\n', 'tasks.svg', TasksView)
        btn_monitor = self.createButton('Monitoreo\n', 'monitor.svg', MonitorView)
        btn_files = self.createButton('Archivos\n', 'files.svg', FilesView)
        btn_control = self.createButton('Control y\ncalibración', 'control.svg', ControlView)
        btn_requests = self.createButton('Solicitudes\n', 'requests.svg', RequestsView)
        btn_users = self.createButton('Usuarios\n', 'users.svg', UsersView)
        btn_inventory = self.createButton('Inventario\n', 'inventory.svg', InventoryView)

        # Menu layout
        layout = QGridLayout()
        layout.addWidget(btn_tasks, 0, 0)
        layout.addWidget(btn_monitor, 0, 1)
        layout.addWidget(btn_files, 0, 2)
        layout.addWidget(btn_control, 0, 3)
        layout.addWidget(btn_requests, 1, 0)
        layout.addWidget(btn_users, 1, 1)
        layout.addWidget(btn_inventory, 1, 2)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def createButton(self, label, icon, viewLink):
        return MainMenuButton(label, icon, viewLink, parent=self)

    def redirectToView(self, view):
        self.parent().changeView(view)
