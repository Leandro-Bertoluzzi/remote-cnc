from PyQt5.QtWidgets import QPushButton
from utils.files import getFileNameInFolder

class MenuButton(QPushButton):
    def __init__(self, text, onClick=None, goToView=None, parent=None):
        super(QPushButton, self).__init__(parent)

        self.setText(text)

        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)
        if onClick:
            self.clicked.connect(onClick)

        stylesheet = getFileNameInFolder(__file__, "MenuButton.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def redirectToView(self):
        self.parent().redirectToView(self.view)