from PyQt5.QtWidgets import QWidget, QVBoxLayout
from components.MenuButton import MenuButton

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Ver cola de ejecución'))
        layout.addWidget(MenuButton('Monitorizar equipo'))
        layout.addWidget(MenuButton('Administrar archivos'))
        layout.addWidget(MenuButton('Control manual y calibración'))
        layout.addWidget(MenuButton('Administrar solicitudes'))
        layout.addWidget(MenuButton('Administrar usuarios'))
        layout.addWidget(MenuButton('Administrar herramientas'))
        self.setLayout(layout)
