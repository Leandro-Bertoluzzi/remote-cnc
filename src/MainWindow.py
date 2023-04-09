from PyQt5.QtWidgets import QMainWindow
from views.MainMenu import MainMenu
from views.UsersView import UsersView

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        entryPoint = MainMenu(onChangeViewToUsers=self.change_view_to_users)
        self.setCentralWidget(entryPoint)
        self.setWindowTitle("CNC admin")

    def change_view_to_users(self):
        centralWidget = UsersView()
        self.setCentralWidget(centralWidget)