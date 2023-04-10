from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from views.UsersView import UsersView

class MainMenu(QWidget):
    def __init__(self, parent=None, onChangeView=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Ver estado de tareas', self.on_button_clicked))
        layout.addWidget(MenuButton('Monitorizar equipo'))
        layout.addWidget(MenuButton('Administrar archivos'))
        layout.addWidget(MenuButton('Control manual y calibración'))
        layout.addWidget(MenuButton('Administrar tareas'))
        layout.addWidget(MenuButton('Administrar usuarios', onChangeView, UsersView, self))
        layout.addWidget(MenuButton('Administrar herramientas'))
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def on_button_clicked(self):
        alert = QMessageBox()
        alert.setText('You clicked the button!')
        alert.exec()