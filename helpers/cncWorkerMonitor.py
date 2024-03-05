from celery.result import AsyncResult
from core.worker.tasks import app
from functools import reduce
from PyQt5.QtCore import QTimer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover

# Constants
STATUS_POLL = 10 * 1000  # miliseconds


class CncWorkerMonitor:
    """Utility class to monitor the status of the active task in worker
    and know if it is finished.
    """
    device_enabled = True

    def __init__(self, window: 'MainWindow'):
        # Attributes definition
        self.window = window
        self.active_task = ''

        # Create and configure timer
        self.monitor = QTimer(self.window)
        self.monitor.setInterval(STATUS_POLL)
        self.monitor.timeout.connect(self.check_task_finished)

    def start_task_monitor(self, task_id: str):
        self.active_task = task_id
        self.monitor.start()

    def stop_task_monitor(self):
        self.monitor.stop()

    def check_task_finished(self):
        task_state = AsyncResult(self.active_task)
        task_status = task_state.status

        if task_status == 'SUCCESS':
            self.set_device_enabled(False)
            self.stop_task_monitor()
            self.window.task_finished()

        if task_status == 'FAILURE':
            task_info = task_state.info
            self.set_device_enabled(False)
            self.stop_task_monitor()
            self.window.task_failed(task_info)

    # STATIC METHODS

    @classmethod
    def is_worker_on(cls):
        try:
            return not not app.control.ping()
        except Exception:
            return False

    @classmethod
    def is_worker_running(cls):
        inspector = app.control.inspect()
        try:
            active_tasks = inspector.active()
            if not active_tasks:
                return False
            tasks_count = reduce(
                lambda x, tasks: x + len(tasks),
                active_tasks.values(),
                0
            )
            return tasks_count > 0
        except Exception:
            return False

    @classmethod
    def get_worker_status(cls):
        inspector = app.control.inspect()

        availability = inspector.ping()
        stats = inspector.stats()
        registered_tasks = inspector.registered()
        active_tasks = inspector.active()
        result = {
            'availability': availability,
            'stats': stats,
            'registered_tasks': registered_tasks,
            'active_tasks': active_tasks
        }
        return result

    @classmethod
    def is_device_enabled(cls):
        return cls.device_enabled

    @classmethod
    def set_device_enabled(cls, enabled: bool):
        cls.device_enabled = enabled
