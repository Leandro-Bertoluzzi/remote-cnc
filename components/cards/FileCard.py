from PyQt5.QtWidgets import QPushButton
from components.cards.Card import Card
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import DuplicatedFileNameError
from core.database.repositories.fileRepository import FileRepository
from core.utils.files import renameFile, deleteFile
from helpers.utils import needs_confirmation


class FileCard(Card):
    def __init__(self, file, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file

        description = f'Archivo {file.id}: {file.file_name}\nUsuario: {file.user.name}'
        editFileBtn = QPushButton("Editar")
        editFileBtn.clicked.connect(self.updateFile)
        removeFileBtn = QPushButton("Borrar")
        removeFileBtn.clicked.connect(self.removeFile)

        self.setDescription(description)
        self.addButton(editFileBtn)
        self.addButton(removeFileBtn)

    def updateFile(self):
        fileDialog = FileDataDialog(self.file)
        if not fileDialog.exec():
            return

        name, path = fileDialog.getInputs()

        if name == self.file.file_name:
            return

        # Checks if the file is repeated
        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.check_file_exists(USER_ID, name, 'impossible-hash')
        except DuplicatedFileNameError:
            self.showWarning(
                'Nombre repetido',
                f'Ya existe un archivo con el nombre <<{name}>>, pruebe renombrarlo'
            )
            return

        # Update file in the file system
        try:
            renameFile(
                self.file.user_id,
                self.file.file_name,
                name
            )
        except Exception as error:
            self.showError(
                'Error de guardado',
                str(error)
            )
            return

        # Update the entry for the file in the DB
        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.update_file(self.file.id, self.file.user_id, name)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.parent().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar el archivo?', 'Eliminar archivo')
    def removeFile(self):
        # Remove the file from the file system
        try:
            deleteFile(self.file.user_id, self.file.file_name)
        except Exception as error:
            self.showError(
                'Error de borrado',
                str(error)
            )
            return

        # Remove the entry for the file in the DB
        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.remove_file(self.file.id)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.parent().refreshLayout()
