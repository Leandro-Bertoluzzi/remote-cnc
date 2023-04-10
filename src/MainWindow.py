from PyQt5.QtWidgets import QMainWindow
from views.MainMenu import MainMenu

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.centralWidget = MainMenu(onChangeView=self.change_view)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle("CNC admin")

    def change_view(self, widget):
        self.centralWidget = widget
        self.setCentralWidget(self.centralWidget)