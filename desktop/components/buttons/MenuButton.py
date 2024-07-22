from PyQt5.QtWidgets import QPushButton
from helpers.utils import applyStylesheet


class MenuButton(QPushButton):
    def __init__(self, text, onClick=None, goToView=None, parent=None):
        super(QPushButton, self).__init__(parent)

        self.setText(text)

        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)
        if onClick:
            self.clicked.connect(onClick)

        applyStylesheet(self, __file__, "MenuButton.qss")

    def redirectToView(self):
        self.parent().redirectToView(self.view)
