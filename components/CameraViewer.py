from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from config import CAMERA_URL


class CameraViewer(QWebEngineView):
    def __init__(self, parent=None):
        super(CameraViewer, self).__init__(parent)

        self.load(QUrl(CAMERA_URL))
        self.connected = True

    def connect(self):
        self.reload()
        self.connected = True

    def disconnect(self):
        self.stop()
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected
