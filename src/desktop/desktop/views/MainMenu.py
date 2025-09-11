from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QWidget

from desktop.components.buttons.MainMenuButton import MainMenuButton
from desktop.views.ControlView import ControlView
from desktop.views.FilesView import FilesView
from desktop.views.InventoryView import InventoryView
from desktop.views.MonitorView import MonitorView
from desktop.views.TasksView import TasksView
from desktop.views.UsersView import UsersView

if TYPE_CHECKING:
    from MainWindow import MainWindow  # pragma: no cover


MENU_OPTIONS = [
    ("Tareas", "tasks.svg", TasksView),
    ("Monitoreo", "monitor.svg", MonitorView),
    ("Archivos", "files.svg", FilesView),
    ("Control y\ncalibración", "control.svg", ControlView),
    ("Usuarios", "users.svg", UsersView),
    ("Inventario", "inventory.svg", InventoryView),
]
GRID_COLUMNS = 4


class MainMenu(QWidget):
    def __init__(self, parent: "MainWindow"):
        super(MainMenu, self).__init__(parent)

        # Populate menu
        layout = QGridLayout()
        for index, (label, icon, view) in enumerate(MENU_OPTIONS):
            x = index // GRID_COLUMNS
            y = index % GRID_COLUMNS
            button = self.createButton(label, icon, view)
            layout.addWidget(button, x, y)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def createButton(self, label, icon, viewLink):
        return MainMenuButton(label, icon, viewLink, parent=self)

    def redirectToView(self, view):
        cast("MainWindow", self.parent()).changeView(view)
