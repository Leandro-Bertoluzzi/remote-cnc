from PyQt5.QtWidgets import QApplication
from utils.config import suppressQtWarnings, loadEnvironmentVariables
import sys

if __name__ == '__main__':
    suppressQtWarnings()
    loadEnvironmentVariables()
    app = QApplication(sys.argv)

    from MainWindow import MainWindow
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
