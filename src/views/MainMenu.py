from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout

class MainMenu(QWidget):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Ver cola de ejecución'))
        layout.addWidget(QPushButton('Monitorizar equipo'))
        layout.addWidget(QPushButton('Administrar archivos'))
        layout.addWidget(QPushButton('Control manual y calibración'))
        layout.addWidget(QPushButton('Administrar solicitudes'))
        layout.addWidget(QPushButton('Administrar usuarios'))
        layout.addWidget(QPushButton('Administrar herramientas'))
        self.setLayout(layout)
