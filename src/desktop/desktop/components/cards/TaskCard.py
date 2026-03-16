import logging

from core.database.models import TASK_DEFAULT_PRIORITY, File, Material, Task, TaskStatus, Tool
from desktop.components.cards.Card import Card
from desktop.components.dialogs.TaskCancelDialog import TaskCancelDialog
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.components.TaskProgress import TaskProgress
from desktop.config import USER_ID
from desktop.helpers.connectionErrors import get_friendly_error_message
from desktop.helpers.utils import needs_confirmation
from desktop.services.deviceService import DeviceService
from desktop.services.taskService import TaskService
from PyQt5.QtWidgets import QPushButton, QSizePolicy

logger = logging.getLogger(__name__)


class TaskCard(Card):
    def __init__(
        self,
        task: Task,
        device_available: bool,
        files: list[File],
        tools: list[Tool],
        materials: list[Material],
        parent=None,
    ):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.device_available = device_available
        self.files = files
        self.tools = tools
        self.materials = materials
        self.setup_ui()

        # Set "status" dynamic property for styling
        self.setProperty("status", task.status)

    # UI MANAGEMENT

    def setup_ui(self):
        self.paused = False
        if self.task.status == TaskStatus.IN_PROGRESS.value:
            try:
                self.paused = DeviceService.is_device_paused()
            except Exception:
                logger.warning("Could not check device paused state")

        self.setup_buttons(self.task.status)

        # Task description
        task_id = self.task.id
        task_name = self.task.name
        task_status_db = self.task.status
        self.setDescription(f"Tarea {task_id}: {task_name}\nEstado: {task_status_db}")

        # Check task status and update if necessary
        self.task_progress = TaskProgress()
        self.check_task_status()

    def check_task_status(self):
        try:
            result = TaskService.get_task_worker_status(self.task.id)
        except Exception:
            logger.warning("Could not query worker status for task %s", self.task.id)
            return

        if result is None:
            return

        task_info = result["info"]
        task_status = result["status"]

        if task_status == "PROGRESS" and self.task.status == TaskStatus.IN_PROGRESS.value:
            self.show_task_progress(task_info)

        if task_status == "FAILURE":
            self.show_task_failure(task_info)

    def show_task_progress(self, task_info):
        sent_lines = task_info.get("sent_lines")
        processed_lines = task_info.get("processed_lines")
        total_lines = task_info.get("total_lines")

        # Progress bar
        self.task_progress.set_total(total_lines)
        self.task_progress.set_progress(sent_lines, processed_lines)

        # Update card layout
        self.task_progress.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.layout().addWidget(self.task_progress)

    def show_task_failure(self, task_info):
        error_msg = task_info
        description_error = f"{self.label_description.text()}\nError: {error_msg}"
        self.setDescription(description_error)

    def setup_buttons(self, status: str):
        """Adds buttons according to task status:

        * pending validation -> | Edit | Approve | Cancel |
        * on hold -> | Cancel | (Run) |
        * in progress -> | Pause/Resume |
        * cancelled -> | Remove | Restore |
        * finished -> | Repeat |
        * failed -> | Retry |
        """

        button_info = {
            TaskStatus.PENDING_APPROVAL.value: [
                ("Editar", self.updateTask),
                ("Aprobar", self.approveTask),
                ("Cancelar", self.cancelTask),
            ],
            TaskStatus.ON_HOLD.value: [("Cancelar", self.cancelTask)],
            TaskStatus.CANCELLED.value: [
                ("Eliminar", self.removeTask),
                ("Restaurar", self.restoreTask),
            ],
            TaskStatus.IN_PROGRESS.value: [
                ("Retomar" if self.paused else "Pausar", self.pauseTask)
            ],
            TaskStatus.FINISHED.value: [("Repetir", self.repeatTask)],
            TaskStatus.FAILED.value: [("Reintentar", self.repeatTask)],
        }

        for status_value, data in button_info.items():
            if status == status_value:
                for button_text, callback in data:
                    self.addButton(button_text, callback)

        if status == TaskStatus.ON_HOLD.value:
            self.addButton("Ejecutar", self.runTask, self.device_available)

    # ACTIONS

    def updateTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            TaskService.update_task(
                self.task.id,
                self.task.user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note,
                TASK_DEFAULT_PRIORITY,
            )
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()

    @needs_confirmation("¿Realmente desea eliminar la tarea?", "Eliminar tarea")
    def removeTask(self):
        try:
            TaskService.remove_task(self.task.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()

    @needs_confirmation(
        "¿Realmente desea restaurar la tarea?"
        "Esto la devolverá al estado inicial, pendiente de aprobación",
        "Restaurar tarea",
    )
    def restoreTask(self):
        self.updateTaskStatus(TaskStatus.INITIAL)
        self.getView().refreshLayout()

    def cancelTask(self):
        cancelDialog = TaskCancelDialog()
        if not cancelDialog.exec():
            return

        cancellation_reason = cancelDialog.getInput()
        self.updateTaskStatus(TaskStatus.CANCELLED, cancellation_reason)
        self.getView().refreshLayout()

    def updateTaskStatus(self, new_status: TaskStatus, cancellation_reason: str = ""):
        try:
            TaskService.update_task_status(
                self.task.id, new_status.value, USER_ID, cancellation_reason
            )
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return

    def repeatTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            TaskService.create_task(self.task.user_id, file_id, tool_id, material_id, name, note)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()

    @needs_confirmation("¿Desea ejecutar la tarea ahora?", "Ejecutar tarea")
    def runTask(self):
        try:
            unavailable_reason = DeviceService.check_device_availability()
        except Exception as error:
            self.showError("Error de conexión", get_friendly_error_message(error))
            return

        if unavailable_reason:
            self.showError("No disponible", unavailable_reason)
            return

        try:
            worker_task_id = TaskService.send_task_to_worker(self.task.id)
        except Exception as error:
            self.showError("Error de conexión", get_friendly_error_message(error))
            return

        self.getWindow().startWorkerMonitor(worker_task_id)
        self.showInformation("Tarea enviada", "Se envió la tarea al equipo para su ejecución")
        self.getView().refreshLayout()

    @needs_confirmation("¿Realmente desea aprobar la solicitud?", "Aprobar solicitud")
    def approveTask(self):
        self.updateTaskStatus(TaskStatus.APPROVED)
        self.getView().refreshLayout()

    def pauseTask(self):
        for i in range(self.layout_buttons.count()):
            widget = self.layout_buttons.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setText("Pausar" if self.paused else "Retomar")

        try:
            if self.paused:
                DeviceService.request_pause()
            else:
                DeviceService.request_resume()
        except Exception as error:
            self.showError("Error de conexión", get_friendly_error_message(error))
            return

        self.paused = not self.paused
