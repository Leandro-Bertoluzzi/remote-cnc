from desktop.presentation.components.StyledWidget import StyledWidget
from PyQt5.QtWidgets import QPushButton


class MenuButton(QPushButton, StyledWidget):
    def __init__(self, text, onClick=None, goToView=None, parent=None):
        super(QPushButton, self).__init__(parent)

        self.setText(text)

        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)
        if onClick:
            self.clicked.connect(onClick)

    def redirectToView(self):
        parent = self.parent()
        if parent is not None:
            parent.redirectToView(self.view)  # type: ignore[attr-defined]
