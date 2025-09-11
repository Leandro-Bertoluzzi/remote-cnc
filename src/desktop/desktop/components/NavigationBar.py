from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget, QPushButton, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from MainWindow import MainWindow  # pragma: no cover


class NavigationWidget(QWidget):
    def __init__(self, options: list, parent=None):
        super(NavigationWidget, self).__init__(parent)

        # Create and set layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # UI configuration
        self.populate(options)

    def populate(self, options: list):
        self.button = QPushButton()
        self.button.setText("PUSH")
        self.layout().addWidget(self.button)


class NavigationBar(QDockWidget):
    def __init__(self, parent: "MainWindow"):
        super(NavigationBar, self).__init__(parent)

        # Configuration:
        # Non movable, only on left area, no title bar
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.setTitleBarWidget(QWidget())

        # Content
        self.sidebar = NavigationWidget([])
        self.setWidget(self.sidebar)
