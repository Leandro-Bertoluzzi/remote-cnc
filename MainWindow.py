from PyQt5.QtWidgets import QMainWindow
from views.MainMenu import MainMenu

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.centralWidget = MainMenu(self)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle("CNC admin")
        self.setStyleSheet("background-color:#333333;");

    def changeView(self, widget):
        self.centralWidget = widget(self)
        self.setCentralWidget(self.centralWidget)

    def backToMenu(self):
        self.centralWidget = MainMenu(self)
        self.setCentralWidget(self.centralWidget)
