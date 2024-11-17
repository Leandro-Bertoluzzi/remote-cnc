from desktop.components.cards.Card import Card
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.components.dialogs.TaskDataDialog import TaskFromFileDialog
from desktop.config import USER_ID, FILES_FOLDER_PATH
from database.base import SessionLocal
from database.exceptions import DatabaseError, EntityNotFoundError
from database.models import File
from database.repositories.fileRepository import DuplicatedFileNameError
from database.repositories.taskRepository import TaskRepository
from database.utils import get_assets
from utilities.files import InvalidFile, FileSystemError
from utilities.fileManager import FileManager
from desktop.helpers.utils import needs_confirmation


class FileCard(Card):
    def __init__(self, file: File, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file

        db_session = SessionLocal()
        self.file_manager = FileManager(FILES_FOLDER_PATH, db_session)
        self.setup_ui()

    def setup_ui(self):
        description = (
            f'Archivo {self.file.id}: {self.file.file_name}\n'
            f'Usuario: {self.file.user.name}'
        )
        self.setDescription(description)

        self.addButton("Crear tarea", self.createTaskFromFile)
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
            self.file_manager.rename_file(USER_ID, self.file, name)
        except DuplicatedFileNameError as error:
            self.showWarning(
                'Nombre repetido',
                str(error)
            )
        except (InvalidFile, FileSystemError) as error:
            self.showError(
                'Error de guardado',
                str(error)
            )
        except (DatabaseError, EntityNotFoundError) as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
        else:
            self.getView().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar el archivo?', 'Eliminar archivo')
    def removeFile(self):
        try:
            self.file_manager.remove_file(self.file)
        except FileSystemError as error:
            self.showError(
                'Error de borrado',
                str(error)
            )
        except (DatabaseError, EntityNotFoundError) as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
        else:
            self.getView().refreshLayout()

    def createTaskFromFile(self):
        try:
            _, materials, tools = get_assets(USER_ID)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        taskDialog = TaskFromFileDialog(self.file, tools, materials)
        if not taskDialog.exec():
            return

        _, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.create_task(USER_ID, self.file.id, tool_id, material_id, name, note)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
