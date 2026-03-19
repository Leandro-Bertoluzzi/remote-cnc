from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QFrame, QLabel, QStatusBar

if TYPE_CHECKING:
    from desktop.MainWindow import MainWindow  # pragma: no cover


class VLine(QFrame):
    """A simple vertical line, to use as a separator."""

    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine | self.Sunken)


class StatusBar(QStatusBar):
    def __init__(self, parent: "MainWindow"):
        super(StatusBar, self).__init__(parent)

        # Components
        self.showMessage("Ready...")
        self.label_worker = QLabel("Worker: ")
        self.label_worker.setStyleSheet("border: 0; color:  blue;")
        self.label_device = QLabel("Dispositivo : ")
        self.label_device.setStyleSheet("border: 0; color:  red;")

        self.reformat()
        self.setStyleSheet("border: 0; background-color: #FFF8DC;")
        self.setStyleSheet("QStatusBar::item {border: none;}")

        self.addPermanentWidget(VLine())
        self.addPermanentWidget(self.label_worker)
        self.addPermanentWidget(VLine())
        self.addPermanentWidget(self.label_device)

    def updateWorkerStatus(self, status: str):
        self.label_worker.setText(f"Worker : {status}")

    def updateDeviceStatus(self, status: str):
        self.label_device.setText(f"Dispositivo : {status}")

    def setStatusMessage(self, message: str):
        self.showMessage(message)

    def setTemporalStatusMessage(self, message: str, duration: int = 2000):
        self.showMessage(message, duration)
