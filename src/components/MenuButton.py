from PyQt5.QtWidgets import QPushButton
from utils.files import getFileNameInFolder

class MenuButton(QPushButton):
    def __init__(self, parent=None, onConnect=None):
        super(QPushButton, self).__init__(parent)

        if onConnect:
            self.clicked.connect(onConnect)

        stylesheet = getFileNameInFolder(__file__, "MenuButton.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())