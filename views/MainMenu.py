from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from views.FilesView import FilesView
from views.InventoryView import InventoryView
from views.RequestsView import RequestsView
from views.UsersView import UsersView
from views.TasksView import TasksView

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QGridLayout()
        layout.addWidget(MenuButton('Ver estado de tareas', goToView=TasksView, parent=self), 1, 1)
        layout.addWidget(MenuButton('Monitorizar equipo'), 1, 2)
        layout.addWidget(MenuButton('Administrar archivos', goToView=FilesView, parent=self), 1, 3)
        layout.addWidget(MenuButton('Calibración'), 1, 4)
        layout.addWidget(MenuButton('Administrar solicitudes', goToView=RequestsView, parent=self), 2, 1)
        layout.addWidget(MenuButton('Administrar usuarios', goToView=UsersView, parent=self), 2, 2)
        layout.addWidget(MenuButton('Administrar inventario', goToView=InventoryView, parent=self), 2, 3)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def redirectToView(self, view):
        self.parent().changeView(view)
