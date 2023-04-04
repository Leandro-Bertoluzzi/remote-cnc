from PyQt5.QtWidgets import QMainWindow
from views.MainMenu import MainMenu

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        entryPoint = MainMenu()
        self.setCentralWidget(entryPoint)
        self.setWindowTitle("CNC admin")