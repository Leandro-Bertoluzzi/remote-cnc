from core.domain.entities import File, Material, Task, Tool
from core.domain.task import TaskStatus
from desktop.presentation.components.cards.Card import Card
from desktop.presentation.components.dialogs.TaskCancelDialog import TaskCancelDialog
from desktop.presentation.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.presentation.components.utils import needs_confirmation
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton


class TaskCard(Card):
    """Presentation-only card for a Task entity."""

    # (task, file_id, tool_id, material_id, name, note)
    update_requested = pyqtSignal(object, int, int, int, str, str)
    # (task,)
    remove_requested = pyqtSignal(object)
    # (task, new_status_value, cancellation_reason)
    status_change_requested = pyqtSignal(object, str, str)
    # (task, file_id, tool_id, material_id, name, note)
    repeat_requested = pyqtSignal(object, int, int, int, str, str)
    # (task,)
    run_requested = pyqtSignal(object)
    # (task, currently_paused)
    pause_resume_requested = pyqtSignal(object, bool)

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

        self.setup_buttons(self.task.status)

        # Task description
        task_id = self.task.id
        task_name = self.task.name
        task_status_db = self.task.status
        self.setDescription(f"Tarea {task_id}: {task_name}\nEstado: {task_status_db}")

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
        self.update_requested.emit(self.task, file_id, tool_id, material_id, name, note)

    @needs_confirmation("¿Realmente desea eliminar la tarea?", "Eliminar tarea")
    def removeTask(self):
        self.remove_requested.emit(self.task)

    @needs_confirmation(
        "¿Realmente desea restaurar la tarea?"
        "Esto la devolverá al estado inicial, pendiente de aprobación",
        "Restaurar tarea",
    )
    def restoreTask(self):
        self.status_change_requested.emit(self.task, TaskStatus.INITIAL.value, "")

    def cancelTask(self):
        cancelDialog = TaskCancelDialog()
        if not cancelDialog.exec():
            return

        cancellation_reason = cancelDialog.getInput()
        self.status_change_requested.emit(
            self.task, TaskStatus.CANCELLED.value, cancellation_reason
        )

    def repeatTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        self.repeat_requested.emit(self.task, file_id, tool_id, material_id, name, note)

    @needs_confirmation("¿Desea ejecutar la tarea ahora?", "Ejecutar tarea")
    def runTask(self):
        self.run_requested.emit(self.task)

    @needs_confirmation("¿Realmente desea aprobar la solicitud?", "Aprobar solicitud")
    def approveTask(self):
        self.status_change_requested.emit(self.task, TaskStatus.APPROVED.value, "")

    def pauseTask(self):
        for i in range(self.layout_buttons.count()):
            widget = self.layout_buttons.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setText("Pausar" if self.paused else "Retomar")

        # Emit before toggling so the view knows the pre-toggle state
        self.pause_resume_requested.emit(self.task, self.paused)
        self.paused = not self.paused
