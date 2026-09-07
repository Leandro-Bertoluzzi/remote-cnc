from core.domain.entities import File, Material, Tool
from manager.adapters.desktop.presentation.components.cards.Card import Card
from manager.adapters.desktop.presentation.components.dialogs.FileDataDialog import FileDataDialog
from manager.adapters.desktop.presentation.components.dialogs.TaskDataDialog import (
    TaskFromFileDialog,
)
from manager.adapters.desktop.presentation.components.utils import needs_confirmation
from PyQt5.QtCore import pyqtSignal


class FileCard(Card):
    """Presentation-only card for a File entity."""

    # (file, new_name)
    rename_requested = pyqtSignal(object, str)
    # (file,)
    remove_requested = pyqtSignal(object)
    # (file, tool_id, material_id, name, note)
    create_task_requested = pyqtSignal(object, int, int, str, str)
    # (file, tool_id, material_id, name, note)
    execute_task_requested = pyqtSignal(object, int, int, str, str)

    def __init__(self, file: File, tools: list[Tool], materials: list[Material], parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file
        self.tools = tools
        self.materials = materials
        self.setup_ui()

    def setup_ui(self):
        user_name = self.file.user.name if self.file.user else "Desconocido"
        description = f"Archivo {self.file.id}: {self.file.file_name}\nUsuario: {user_name}"
        self.setDescription(description)

        self.addButton("Crear tarea", self.createTaskFromFile)
        self.addButton("Ejecutar", self.executeTaskFromFile)
        self.addButton("Editar", self.updateFile)
        self.addButton("Borrar", self.removeFile)

    def updateFile(self):
        fileDialog = FileDataDialog(self.file)
        if not fileDialog.exec():
            return

        name, _ = fileDialog.getInputs()

        if name == self.file.file_name:
            return

        self.rename_requested.emit(self.file, name)

    @needs_confirmation("¿Realmente desea eliminar el archivo?", "Eliminar archivo")
    def removeFile(self):
        self.remove_requested.emit(self.file)

    def _open_task_dialog(self):
        """Open the task-from-file dialog and return user inputs, or None if cancelled."""
        taskDialog = TaskFromFileDialog(self.file, self.tools, self.materials)
        if not taskDialog.exec():
            return None
        return taskDialog.getInputs()

    def createTaskFromFile(self):
        task_config = self._open_task_dialog()
        if not task_config:
            return

        _, tool_id, material_id, name, note = task_config
        self.create_task_requested.emit(self.file, tool_id, material_id, name, note)

    @needs_confirmation("¿Desea ejecutar la tarea ahora?", "Ejecutar tarea")
    def executeTaskFromFile(self):
        task_config = self._open_task_dialog()
        if not task_config:
            return

        _, tool_id, material_id, name, note = task_config
        self.execute_task_requested.emit(self.file, tool_id, material_id, name, note)
