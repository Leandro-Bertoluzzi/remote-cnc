import logging
from typing import TYPE_CHECKING

from desktop.components.cards.TaskCard import TaskCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.config import USER_ID
from desktop.helpers.connectionErrors import get_friendly_error_message
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.taskService import TaskService
from desktop.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from MainWindow import MainWindow  # pragma: no cover

logger = logging.getLogger(__name__)


class TasksView(BaseListView):
    def __init__(self, parent: "MainWindow"):
        super(TasksView, self).__init__(parent)

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
