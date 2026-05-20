from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PyQt5.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from desktop.app_context import AppContext  # pragma: no cover
    from desktop.MainWindow import MainWindow  # pragma: no cover


class BaseView(QWidget):
    def __init__(self, parent: "MainWindow", context: "AppContext | None" = None):
        super(BaseView, self).__init__(parent)
        self._context = context

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
