from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from components.buttons.MainMenuButton import MainMenuButton
from views.FilesView import FilesView
from views.InventoryView import InventoryView
from views.RequestsView import RequestsView
from views.UsersView import UsersView
from views.TasksView import TasksView

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QGridLayout()
        layout.addWidget(MainMenuButton('Administrar\ntareas', 'button.png', TasksView, parent=self), 1, 1)
        layout.addWidget(MainMenuButton('Monitorizar\nequipo', 'button.png'), 1, 2)
        layout.addWidget(MainMenuButton('Administrar\narchivos', 'button.png', FilesView, parent=self), 1, 3)
        layout.addWidget(MainMenuButton('Control manual\ny calibración', 'control.svg'), 1, 4)
        layout.addWidget(MainMenuButton('Administrar\nsolicitudes', 'button.png', RequestsView, parent=self), 2, 1)
        layout.addWidget(MainMenuButton('Administrar\nusuarios', 'button.png', UsersView, parent=self), 2, 2)
        layout.addWidget(MainMenuButton('Administrar\ninventario', 'button.png', InventoryView, parent=self), 2, 3)
        #layout.addWidget(MainMenuButton('xxx', 'button.png'), 2, 4)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def redirectToView(self, view):
        self.parent().changeView(view)
