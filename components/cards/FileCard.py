from components.cards.Card import Card
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.exceptions import DatabaseError, EntityNotFoundError
from core.database.models import File
from core.database.repositories.fileRepository import DuplicatedFileNameError
from core.database.repositories.fileRepository import FileRepository
from core.utils.files import renameFile, deleteFile, InvalidFile, FileSystemError
from helpers.utils import needs_confirmation


class FileCard(Card):
    def __init__(self, file: File, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file
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
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            # Check if the file is repeated
            repository.check_file_exists(USER_ID, name, 'impossible-hash')
            # Update file in the file system
            renameFile(
                self.file.user_id,
                self.file.file_name,
                name
            )
            # Update the entry for the file in the DB
            repository.update_file(self.file.id, self.file.user_id, name)
        except DuplicatedFileNameError:
            self.showWarning(
                'Nombre repetido',
                f'Ya existe un archivo con el nombre <<{name}>>, pruebe renombrarlo'
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
        except Exception as error:
            self.showError(
                'Error',
                str(error)
            )
        else:
            self.getView().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar el archivo?', 'Eliminar archivo')
    def removeFile(self):
        try:
            # Remove the file from the file system
            deleteFile(self.file.user_id, self.file.file_name)
            # Remove the entry for the file in the DB
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.remove_file(self.file.id)
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
