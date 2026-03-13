#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
from desktop.config import suppressQtWarnings
from desktop.MainWindow import MainWindow
import sys

if __name__ == '__main__':
    suppressQtWarnings()
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
