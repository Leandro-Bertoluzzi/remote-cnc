#!/usr/bin/env python3

import os
import sys

from PyQt5.QtWidgets import QApplication

from desktop.app_context import AppContext, create_app_context
from desktop.MainWindow import MainWindow
from desktop.services import configure_session_factory, deviceService, fileService, taskService


def _configure_services(context: AppContext) -> None:
    """Wire all service modules with the port implementations from ``AppContext``.

    This is the single call that replaces every lazy singleton that services
    used to create internally. Must be called before any service method runs.
    """
    configure_session_factory(context.session_factory)
    deviceService.configure(context.gateway, context.worker)
    taskService.configure(context.worker)
    fileService.configure(context.worker, context.file_storage)


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
    _configure_services(context)
    mainWindow = MainWindow(context)
    mainWindow.show()
    sys.exit(app.exec())
