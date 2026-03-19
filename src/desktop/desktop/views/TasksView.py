import logging
from typing import TYPE_CHECKING, cast

from core.database.models import TaskStatus
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QVBoxLayout

from desktop.components.cards.TaskCard import TaskCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.components.TaskProgress import TaskProgress
from desktop.config import USER_ID
from desktop.helpers.connectionErrors import get_friendly_error_message
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.taskService import TaskService
from desktop.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from desktop.MainWindow import MainWindow  # pragma: no cover

logger = logging.getLogger(__name__)


class TasksView(BaseListView):
    def __init__(self, parent: "MainWindow"):
        super(TasksView, self).__init__(parent)

        self._progress_connected = False

        try:
            self.files, self.materials, self.tools = AssetService.get_assets(USER_ID)
        except Exception as error:
            error_msg = get_friendly_error_message(error)
            self.layout().addWidget(
                ConnectionErrorWidget(
                    error_msg,
                    retry_callback=lambda: parent.changeView(TasksView),
                    back_callback=parent.backToMenu,
                    parent=self,
                )
            )
            return

        # Task progress bar — shown above the card list when a task is running
        self.task_progress = TaskProgress(parent=self)
        self.task_progress.setVisible(False)

        self.setItemListFromValues(
            "TAREAS",
            "La cola de tareas está vacía",
            self.createTaskCard,
            "Crear tarea",
            self.createTask,
        )
        self.refreshLayout()

    def createTaskCard(self, task):
        return TaskCard(
            task, self.device_available, self.files, self.tools, self.materials, parent=self
        )

    def getItems(self):
        tasks = TaskService.get_all_tasks(USER_ID, status="all")

        # Check if there is a task in progress
        try:
            self.device_available = DeviceService.is_device_available()
        except Exception:
            logger.warning("Could not check device availability")
            self.device_available = False

        return tasks

    def refreshLayout(self):
        """Re-draw the view, inserting the progress bar at the top when applicable."""
        super().refreshLayout()

        # Show progress bar if a task is currently running
        has_running_task = any(
            item
            for view_list in self.lists
            for item in view_list["items"]
            if getattr(item, "status", None) == TaskStatus.IN_PROGRESS.value
        )
        if has_running_task and hasattr(self, "task_progress"):
            self.task_progress.setVisible(True)
            cast(QVBoxLayout, self.layout()).insertWidget(0, self.task_progress)
            self._connect_progress_signals()
        elif hasattr(self, "task_progress"):
            self.task_progress.setVisible(False)
            self._disconnect_progress_signals()

    # Signal management

    def _connect_progress_signals(self):
        """Connect GatewayMonitor signals for real-time progress updates."""
        if self._progress_connected:
            return
        monitor = self.getWindow().worker_monitor
        monitor.file_progress.connect(self._on_file_progress)
        monitor.file_finished.connect(self._on_file_finished)
        monitor.file_failed.connect(self._on_file_failed)
        self._progress_connected = True

    def _disconnect_progress_signals(self):
        """Disconnect GatewayMonitor signals."""
        if not self._progress_connected:
            return
        try:
            monitor = self.getWindow().worker_monitor
            monitor.file_progress.disconnect(self._on_file_progress)
            monitor.file_finished.disconnect(self._on_file_finished)
            monitor.file_failed.disconnect(self._on_file_failed)
        except (RuntimeError, TypeError):
            pass
        self._progress_connected = False

    # Slots

    def _on_file_progress(self, sent: int, processed: int, total: int):
        self.task_progress.set_total(total)
        self.task_progress.set_progress(sent, processed)

    def _on_file_finished(self):
        self.task_progress.setVisible(False)
        self._disconnect_progress_signals()
        self.refreshLayout()

    def _on_file_failed(self, _error_msg: str):
        self.task_progress.setVisible(False)
        self._disconnect_progress_signals()
        self.refreshLayout()

    # Cleanup

    def closeEvent(self, a0: QCloseEvent):
        self._disconnect_progress_signals()
        super().closeEvent(a0)

    def createTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            TaskService.create_task(USER_ID, file_id, tool_id, material_id, name, note)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()
