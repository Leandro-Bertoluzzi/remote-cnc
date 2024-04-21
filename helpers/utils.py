from config import USER_ID, PROJECT_ROOT, SERIAL_BAUDRATE, SERIAL_PORT
from core.utils.files import getFileNameInFolder
from core.utils.storage import add_value_with_id
from core.worker import executeTask
from PyQt5.QtWidgets import QMessageBox, QWidget


# Functions
def applyStylesheet(self: QWidget, current_file: str, styles_file: str):
    """Apply custom styles to the widget.
    """
    stylesheet = getFileNameInFolder(current_file, styles_file)
    with open(stylesheet, "r") as styles:
        self.setStyleSheet(styles.read())


def send_task_to_worker(db_task_id: int) -> str:
    """Request the task to be executed by the worker.
    """
    worker_task = executeTask.delay(
        db_task_id,
        USER_ID,
        PROJECT_ROOT,
        SERIAL_PORT,
        SERIAL_BAUDRATE
    )
    add_value_with_id('task', id=db_task_id, value=worker_task.task_id)

    return worker_task.task_id


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
