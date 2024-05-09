from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QToolBar, QToolButton
from typing import Callable

# Custom types
ToolBarOptionInfo = tuple[str, Callable[[], None], bool]
ToolBarOptionRefs = dict[str, QToolButton]


class ToolBar(QToolBar):
    """Adds a custom tool bar to the window
    """
    def __init__(self, options: list[ToolBarOptionInfo], window: QMainWindow, parent=None):
        super(ToolBar, self).__init__(parent)

        self.setMovable(False)
        window.addToolBar(Qt.TopToolBarArea, self)

        self.options: ToolBarOptionRefs = {}
        self.add_options(options)

    # SETTERS

    def add_option(self, option: ToolBarOptionInfo):
        (label, action, checkable) = option
        tool_button = QToolButton()
        tool_button.setText(label)
        tool_button.setCheckable(checkable)
        tool_button.clicked.connect(action)
        self.addWidget(tool_button)

        self.options[label.lower()] = tool_button

    def add_options(self, options: list[ToolBarOptionInfo]):
        for option in options:
            self.add_option(option)

    # GETTERS

    def get_options(self) -> ToolBarOptionRefs:
        return self.options
