from celery.result import AsyncResult
from core.worker.tasks import app
from functools import reduce
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Constants
STATUS_POLL = 100  # miliseconds


class CncWorkerMonitor(QObject):
    """Utility class to monitor the status of the active task in worker
    and know if it is finished.
    """
    # CLASS ATTRIBUTES
    device_enabled = True

    # SIGNALS

    task_new_status = pyqtSignal(int, int, int, object, object)
    task_finished = pyqtSignal()
    task_failed = pyqtSignal(str)

    # CONSTRUCTOR

    def __init__(self):
        super().__init__()

        # Attributes definition
        self.active_task = ''

        # Create and configure timer
        self.monitor = QTimer(self)
        self.monitor.setInterval(STATUS_POLL)
        self.monitor.timeout.connect(self.check_task_status)

    # FLOW CONTROL

    def start_task_monitor(
        self,
        task_id: str
    ):
        self.active_task = task_id
        self.monitor.start()

    def stop_task_monitor(self):
        self.monitor.stop()

    # SLOTS

    def check_task_status(self):
        task_state = AsyncResult(self.active_task)
        task_info = task_state.info
        task_status = task_state.status

        if task_status == 'PROGRESS':
            sent_lines = task_info.get('sent_lines')
            processed_lines = task_info.get('processed_lines')
            total_lines = task_info.get('total_lines')
            controller_status = task_info.get('status')
            grbl_parserstate = task_info.get('parserstate')

            self.task_new_status.emit(
                sent_lines,
                processed_lines,
                total_lines,
                controller_status,
                grbl_parserstate
            )

        if task_status == 'SUCCESS':
            self.set_device_enabled(False)
            self.stop_task_monitor()
            self.task_finished.emit()

        if task_status == 'FAILURE':
            self.set_device_enabled(False)
            self.stop_task_monitor()
            self.task_failed.emit(str(task_info))

    # STATIC METHODS

    @classmethod
    def is_worker_on(cls):
        """Returns whether the worker process is running.
        """
        try:
            return not not app.control.ping()
        except Exception:
            return False

    @classmethod
    def is_worker_running(cls):
        """Returns whether the worker process is working on a task.
        """
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
    def is_device_available(cls):
        """Checks if device is ready for use (enabled + not running)
        """
        return cls.device_enabled and not cls.is_worker_running()

    @classmethod
    def set_device_enabled(cls, enabled: bool):
        cls.device_enabled = enabled
