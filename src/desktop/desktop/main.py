#!/usr/bin/env python3

import os
import sys

from PyQt5.QtWidgets import QApplication

from desktop.app_context import create_app_context
from desktop.MainWindow import MainWindow


def suppressQtWarnings():
    """Suppresses common Qt warnings about high DPI scaling on Windows."""
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"


if __name__ == "__main__":
    suppressQtWarnings()
    app = QApplication(sys.argv)
    context = create_app_context()
    mainWindow = MainWindow(context)
    mainWindow.show()
    sys.exit(app.exec())
