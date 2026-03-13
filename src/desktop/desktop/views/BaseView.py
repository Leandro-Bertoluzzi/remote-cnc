from PyQt5.QtWidgets import QMessageBox, QWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class BaseView(QWidget):
    def __init__(self, parent: 'MainWindow'):
        super(BaseView, self).__init__(parent)

    # Notifications

    def showInfo(self, title, text):
        QMessageBox.information(self, title, text, QMessageBox.Ok)

    def showWarning(self, title, text):
        QMessageBox.warning(self, title, text, QMessageBox.Ok)

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)

    # Helper methods

    def getWindow(self) -> 'MainWindow':
        return self.parent()    # type: ignore
