from PyQt5.QtWidgets import QApplication
from views.MainMenu import MainMenu
from MainWindow import MainWindow
from utils.config import suppressQtWarnings

if __name__ == '__main__':
    suppressQtWarnings()
    import sys

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    entryPoint = MainMenu()
    mainWindow.setCentralWidget(entryPoint)
    mainWindow.show()
    sys.exit(app.exec())