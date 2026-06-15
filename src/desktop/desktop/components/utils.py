from pathlib import Path

from PyQt5.QtWidgets import QMessageBox


# Functions
def get_file_name_in_folder(current: str, searched: str) -> Path:
    """Generates the absolute path to a file in the same folder

    Parameter(s):
    - current: string, path to the reference file
    - searched: string, file name of the searched file
    """
    folder = Path(current).parent
    return folder / searched


# Decorators
def needs_confirmation(text, title):
    """[Decorator] Shows a confirmation dialog before executing the decorated function."""

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
