from typing import TYPE_CHECKING, cast

from PyQt5.QtWidgets import QMessageBox, QWidget

if TYPE_CHECKING:
    from desktop.MainWindow import MainWindow  # pragma: no cover


class BaseView(QWidget):
    def __init__(self, parent: "MainWindow"):
        super(BaseView, self).__init__(parent)

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
