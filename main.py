from PyQt5.QtWidgets import QApplication
from config import suppressQtWarnings
import sys

if __name__ == '__main__':
    suppressQtWarnings()
    app = QApplication(sys.argv)

    from MainWindow import MainWindow
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
