from collections.abc import Callable
from desktop.helpers.utils import applyStylesheet
from desktop.views.BaseView import BaseView
from PyQt5.QtWidgets import QPushButton, QWidget
from typing import Optional


class MenuButton(QPushButton):
    def __init__(
            self,
            text: str,
            onClick: Optional[Callable[[], None]] = None,
            goToView: Optional[BaseView] = None,
            parent: Optional[QWidget] = None
        ):
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
