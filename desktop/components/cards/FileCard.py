from components.cards.Card import Card
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID, FILES_FOLDER_PATH
from core.database.exceptions import DatabaseError, EntityNotFoundError
from core.database.models import File
from core.database.repositories.fileRepository import DuplicatedFileNameError
from core.utils.files import InvalidFile, FileSystemError
from core.utils.fileManager import FileManager
from helpers.utils import needs_confirmation


class FileCard(Card):
    def __init__(self, file: File, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file
        self.file_manager = FileManager(FILES_FOLDER_PATH)
        self.setup_ui()

    def setup_ui(self):
        description = (
            f'Archivo {self.file.id}: {self.file.file_name}\n'
            f'Usuario: {self.file.user.name}'
        )
        self.setDescription(description)

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
