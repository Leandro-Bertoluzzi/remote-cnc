import inspect

from desktop.presentation.components.utils import get_file_name_in_folder
from PyQt5.QtWidgets import QWidget


class StyledWidget(QWidget):
    def __init__(self, parent=None):
        super(StyledWidget, self).__init__(parent)
        self._apply_stylesheet()

    def _apply_stylesheet(self: QWidget):
        """Apply <WidgetClassName>.qss from the same folder as the widget class file."""
        current_file = inspect.getfile(self.__class__)
        styles_file = f"{self.__class__.__name__}.qss"
        stylesheet = get_file_name_in_folder(current_file, styles_file)

        if stylesheet.exists():
            with open(stylesheet, "r", encoding="utf-8") as styles:
                self.setStyleSheet(styles.read())
