from collections.abc import Callable

from desktop.helpers.utils import applyStylesheet
from desktop.views.BaseView import BaseView
from PyQt5.QtWidgets import QPushButton, QWidget


class MenuButton(QPushButton):
    def __init__(
        self,
        text: str,
        onClick: Callable[[], None] | None = None,
        goToView: type[BaseView] | None = None,
        parent: QWidget | None = None,
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
        parent = self.parent()
        if parent is not None:
            parent.redirectToView(self.view)  # type: ignore[attr-defined]
