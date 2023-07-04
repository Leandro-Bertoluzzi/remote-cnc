from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from utils.config import suppressQtWarnings
import sys

if __name__ == '__main__':
    suppressQtWarnings()
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
