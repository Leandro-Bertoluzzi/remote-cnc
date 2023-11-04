from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from views.FilesView import FilesView
from views.InventoryView import InventoryView
from views.RequestsView import RequestsView
from views.UsersView import UsersView
from views.TasksView import TasksView

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QGridLayout()
        layout.addWidget(MenuButton('Administrar\ntareas', goToView=TasksView, parent=self), 1, 1)
        layout.addWidget(MenuButton('Monitorizar\nequipo'), 1, 2)
        layout.addWidget(MenuButton('Administrar\narchivos', goToView=FilesView, parent=self), 1, 3)
        layout.addWidget(MenuButton('Control manual\ny calibración'), 1, 4)
        layout.addWidget(MenuButton('Administrar\nsolicitudes', goToView=RequestsView, parent=self), 2, 1)
        layout.addWidget(MenuButton('Administrar\nusuarios', goToView=UsersView, parent=self), 2, 2)
        layout.addWidget(MenuButton('Administrar\ninventario', goToView=InventoryView, parent=self), 2, 3)
        layout.addWidget(MenuButton('xxx'), 2, 4)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def redirectToView(self, view):
        self.parent().changeView(view)
