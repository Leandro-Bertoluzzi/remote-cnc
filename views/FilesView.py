from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import DuplicatedFileError, \
    DuplicatedFileNameError, FileRepository
from core.utils.files import computeSHA256, copyFile
from views.BaseListView import BaseListView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class FilesView(BaseListView):
    def __init__(self, parent: 'MainWindow'):
        super(FilesView, self).__init__(parent)
        self.setItemListFromValues(
            'ARCHIVOS',
            'Aún no hay archivos almacenados',
            self.createFileCard,
            'Subir archivo',
            self.createFile
        )
        self.refreshLayout()

    def createFileCard(self, item):
        return FileCard(item, self)

    def getItems(self):
        db_session = SessionLocal()
        repository = FileRepository(db_session)
        return repository.get_all_files()

    def createFile(self):
        fileDialog = FileDataDialog()
        if not fileDialog.exec():
            return

        name, path = fileDialog.getInputs()

        # Checks if the file is repeated
        file_hash = computeSHA256(path)
        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.check_file_exists(USER_ID, name, file_hash)
        except DuplicatedFileNameError:
            self.showWarning(
                'Nombre repetido',
                f'Ya existe un archivo con el nombre <<{name}>>, pruebe renombrarlo'
            )
            return
        except DuplicatedFileError as error:
            self.showWarning(
                'Archivo repetido',
                str(error)
            )
            return

        # Save file in the file system
        try:
            copyFile(USER_ID, path, name)
        except Exception as error:
            self.showError(
                'Error de guardado',
                str(error)
            )
            return

        # Create an entry for the file in the DB
        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            repository.create_file(USER_ID, name, file_hash)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.refreshLayout()
