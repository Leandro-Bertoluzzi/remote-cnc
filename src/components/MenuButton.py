from PyQt5.QtWidgets import QPushButton
from utils.files import getFileNameInFolder

class MenuButton(QPushButton):
    def __init__(self, text, onConnect=None, goToView=None, parent=None):
        super(QPushButton, self).__init__(parent)

        self.setText(text)

        if onConnect and goToView:
            self.onConnect = onConnect
            self.view = goToView()
            self.clicked.connect(self.redirectToView)
        elif onConnect:
            self.clicked.connect(onConnect)

        stylesheet = getFileNameInFolder(__file__, "MenuButton.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())
    
    def redirectToView(self):
        self.onConnect(self.view)