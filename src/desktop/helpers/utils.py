from utilities.files import getFileNameInFolder
from PyQt5.QtWidgets import QMessageBox, QWidget


# Functions
def applyStylesheet(self: QWidget, current_file: str, styles_file: str):
    """Apply custom styles to the widget.
    """
    stylesheet = getFileNameInFolder(current_file, styles_file)
    with open(stylesheet, "r") as styles:
        self.setStyleSheet(styles.read())


# Decorators
def needs_confirmation(text, title):
    """[Decorator] Shows a confirmation dialog before executing the decorated function.
    """
    def decorator(fun):
        def wrapper(*args):
            confirmation = QMessageBox()
            confirmation.setIcon(QMessageBox.Question)
            confirmation.setText(text)
            confirmation.setWindowTitle(title)
            confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if confirmation.exec() != QMessageBox.Yes:
                return

            # We only send the 'self' argument, ignoring all possible
            # additional arguments added by the function being a slot
            return fun(args[0])
        return wrapper
    return decorator
