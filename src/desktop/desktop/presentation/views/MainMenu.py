from typing import TYPE_CHECKING, cast

from desktop.presentation.components.buttons.MainMenuButton import MainMenuButton
from desktop.presentation.views.ControlView import ControlView
from desktop.presentation.views.FilesView import FilesView
from desktop.presentation.views.InventoryView import InventoryView
from desktop.presentation.views.MonitorView import MonitorView
from desktop.presentation.views.TasksView import TasksView
from desktop.presentation.views.UsersView import UsersView
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QWidget

if TYPE_CHECKING:
    from desktop.presentation.MainWindow import MainWindow  # pragma: no cover


class MainMenu(QWidget):
    def __init__(self, parent: "MainWindow"):
        super(MainMenu, self).__init__(parent)

        # Buttons
        btn_tasks = self.createButton("Tareas", "tasks.svg", TasksView)
        btn_monitor = self.createButton("Monitoreo", "monitor.svg", MonitorView)
        btn_files = self.createButton("Archivos", "files.svg", FilesView)
        btn_control = self.createButton("Control y\ncalibración", "control.svg", ControlView)
        btn_users = self.createButton("Usuarios", "users.svg", UsersView)
        btn_inventory = self.createButton("Inventario", "inventory.svg", InventoryView)

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
        cast("MainWindow", self.parent()).changeView(view)
