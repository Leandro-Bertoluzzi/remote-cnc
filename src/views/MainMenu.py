from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Ver estado de tareas', on_button_clicked))
        layout.addWidget(MenuButton('Monitorizar equipo'))
        layout.addWidget(MenuButton('Administrar archivos'))
        layout.addWidget(MenuButton('Control manual y calibración'))
        layout.addWidget(MenuButton('Administrar tareas'))
        layout.addWidget(MenuButton('Administrar usuarios'))
        layout.addWidget(MenuButton('Administrar herramientas'))
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

def on_button_clicked():
    alert = QMessageBox()
    alert.setText('You clicked the button!')
    alert.exec()