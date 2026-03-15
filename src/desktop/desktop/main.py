#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QApplication

from desktop.config import suppressQtWarnings
from desktop.MainWindow import MainWindow

if __name__ == "__main__":
    suppressQtWarnings()
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
