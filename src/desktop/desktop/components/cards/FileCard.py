import logging

from core.database.exceptions import DatabaseError, EntityNotFoundError
from core.database.models import File
from core.database.repositories.fileRepository import DuplicatedFileNameError
from core.utilities.files import FileSystemError, InvalidFile
from desktop.components.cards.Card import Card
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.components.dialogs.TaskDataDialog import TaskFromFileDialog
from desktop.config import USER_ID
from desktop.helpers.connectionErrors import get_friendly_error_message
from desktop.helpers.utils import needs_confirmation
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.fileService import FileService
from desktop.services.taskService import TaskService

logger = logging.getLogger(__name__)


class FileCard(Card):
    def __init__(self, file: File, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file
        self.setup_ui()

    def setup_ui(self):
        description = (
            f"Archivo {self.file.id}: {self.file.file_name}\nUsuario: {self.file.user.name}"
        )
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

        try:
            FileService.rename_file(USER_ID, self.file, name)
        except DuplicatedFileNameError as error:
            self.showWarning("Nombre repetido", str(error))
        except (InvalidFile, FileSystemError) as error:
            self.showError("Error de guardado", str(error))
        except (DatabaseError, EntityNotFoundError) as error:
            self.showError("Error de base de datos", str(error))
        else:
            self.getView().refreshLayout()

    @needs_confirmation("¿Realmente desea eliminar el archivo?", "Eliminar archivo")
    def removeFile(self):
        try:
            FileService.remove_file(self.file)
        except FileSystemError as error:
            self.showError("Error de borrado", str(error))
        except (DatabaseError, EntityNotFoundError) as error:
            self.showError("Error de base de datos", str(error))
        else:
            self.getView().refreshLayout()

    def _create_task_dialog(self):
        try:
            _, materials, tools = AssetService.get_assets(USER_ID)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return

        taskDialog = TaskFromFileDialog(self.file, tools, materials)
        if not taskDialog.exec():
            return

        return taskDialog.getInputs()

    def createTaskFromFile(self):
        task_config = self._create_task_dialog()
        if not task_config:
            return

        _, tool_id, material_id, name, note = task_config

        try:
            TaskService.create_task(USER_ID, self.file.id, tool_id, material_id, name, note)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return

    @needs_confirmation("¿Desea ejecutar la tarea ahora?", "Ejecutar tarea")
    def executeTaskFromFile(self):
        try:
            unavailable_reason = DeviceService.check_device_availability()
        except Exception as error:
            self.showError("Error de conexión", get_friendly_error_message(error))
            return

        if unavailable_reason:
            self.showError("No disponible", unavailable_reason)
            return

        task_config = self._create_task_dialog()
        if not task_config:
            return

        _, tool_id, material_id, name, note = task_config

        try:
            TaskService.create_and_execute_task(
                USER_ID, self.file.id, tool_id, material_id, name, note
            )
        except Exception as error:
            self.showError("Error", str(error))
            return

        self.getWindow().startWorkerMonitor()
        self.showInformation("Tarea enviada", "Se envió la tarea al equipo para su ejecución")
