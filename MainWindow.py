from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QCloseEvent
from views.MainMenu import MainMenu


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setCentralWidget(MainMenu(self))
        self.setWindowTitle("CNC admin")
        self.setStyleSheet("background-color:#666666;")

    def changeView(self, widget):
        self.setCentralWidget(widget(self))

    def backToMenu(self):
        self.setCentralWidget(MainMenu(self))

    def closeEvent(self, event: QCloseEvent):
        confirmation = QMessageBox.question(
            self,
            'Cerrar aplicación',
            '¿Realmente desea cerrar la aplicación?',
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if confirmation == QMessageBox.Yes:
            self.centralWidget().closeEvent(event)
            event.accept()
        else:
            event.ignore()
