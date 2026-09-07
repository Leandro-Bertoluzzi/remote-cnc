from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from manager.adapters.desktop.context import AppContext  # pragma: no cover
    from manager.adapters.desktop.presentation.MainWindow import MainWindow  # pragma: no cover


class BaseView(QWidget):
    # Emitted when the user requests to return to the main menu.
    back_requested = pyqtSignal()
    # Emitted when a toolbar should be registered with the main window.
    toolbar_added = pyqtSignal(object)
    # Emitted when a toolbar should be removed from the main window.
    toolbar_removed = pyqtSignal(object)
    # Emitted after a task has been dispatched to the worker.
    task_dispatched = pyqtSignal()

    def __init__(self, parent: "MainWindow", context: "AppContext | None" = None, **kwargs):
        super(BaseView, self).__init__(parent)
        # Prefer the explicitly-supplied context; fall back to parent._context so
        # tests and MainMenu can create views without forwarding the context manually.
        self._context = context if context is not None else parent._context

    # Notifications

    def showInfo(self, title, text):
        QMessageBox.information(self, title, text, QMessageBox.Ok)

    def showWarning(self, title, text):
        QMessageBox.warning(self, title, text, QMessageBox.Ok)

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)

    # Events

    def back_to_menu(self):
        self.back_requested.emit()
