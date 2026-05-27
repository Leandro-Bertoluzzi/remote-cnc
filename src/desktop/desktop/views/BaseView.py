from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PyQt5.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from desktop.app_context import AppContext  # pragma: no cover
    from desktop.MainWindow import MainWindow  # pragma: no cover


class BaseView(QWidget):
    def __init__(self, parent: "MainWindow", context: "AppContext | None" = None):
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

    # Helper methods

    def getWindow(self) -> "MainWindow":
        return cast("MainWindow", self.parent())
