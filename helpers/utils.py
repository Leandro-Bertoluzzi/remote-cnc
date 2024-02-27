from core.utils.files import getFileNameInFolder
from PyQt5.QtWidgets import QMessageBox, QWidget


# Functions
def applyStylesheet(self: QWidget, current_file: str, styles_file: str):
    # Apply custom styles
    stylesheet = getFileNameInFolder(current_file, styles_file)
    with open(stylesheet, "r") as styles:
        self.setStyleSheet(styles.read())


# Decorators
def needs_confirmation(text, title):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            confirmation = QMessageBox()
            confirmation.setIcon(QMessageBox.Question)
            confirmation.setText(text)
            confirmation.setWindowTitle(title)
            confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if confirmation.exec() != QMessageBox.Yes:
                return

            return fun(*args, **kwargs)
        return wrapper
    return decorator
