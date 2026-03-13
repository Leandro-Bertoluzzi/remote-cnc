from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from desktop.components.buttons.MainMenuButton import MainMenuButton
from desktop.views.ControlView import ControlView
from desktop.views.FilesView import FilesView
from desktop.views.InventoryView import InventoryView
from desktop.views.MonitorView import MonitorView
from desktop.views.UsersView import UsersView
from desktop.views.TasksView import TasksView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class MainMenu(QWidget):
    def __init__(self, parent: 'MainWindow'):
        super(MainMenu, self).__init__(parent)

        # Buttons
        btn_tasks = self.createButton('Tareas', 'tasks.svg', TasksView)
        btn_monitor = self.createButton('Monitoreo', 'monitor.svg', MonitorView)
        btn_files = self.createButton('Archivos', 'files.svg', FilesView)
        btn_control = self.createButton('Control y\ncalibración', 'control.svg', ControlView)
        btn_users = self.createButton('Usuarios', 'users.svg', UsersView)
        btn_inventory = self.createButton('Inventario', 'inventory.svg', InventoryView)

        # Menu layout
        layout = QGridLayout()
        layout.addWidget(btn_tasks, 0, 0)
        layout.addWidget(btn_monitor, 0, 1)
        layout.addWidget(btn_files, 0, 2)
        layout.addWidget(btn_control, 0, 3)
        layout.addWidget(btn_users, 1, 0)
        layout.addWidget(btn_inventory, 1, 1)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def createButton(self, label, icon, viewLink):
        return MainMenuButton(label, icon, viewLink, parent=self)

    def redirectToView(self, view):
        self.parent().changeView(view)
