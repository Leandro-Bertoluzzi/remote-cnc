from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID, FILES_FOLDER_PATH
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import DuplicatedFileError, \
    DuplicatedFileNameError, DatabaseError, FileRepository
from core.utils.files import InvalidFile, FileSystemError
from core.utils.fileManager import FileManager
from core.worker.scheduler import createThumbnail, generateFileReport
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

        file_manager = FileManager(FILES_FOLDER_PATH)
        try:
            file_id = file_manager.create_file(USER_ID, name, path)
            generateFileReport.delay(file_id)
            createThumbnail.delay(file_id)
        except (DuplicatedFileNameError, DuplicatedFileError) as error:
            self.showWarning(
                'Archivo repetido',
                str(error)
            )
            return
        except (InvalidFile, FileSystemError) as error:
            self.showError(
                'Error de guardado',
                str(error)
            )
            return
        except DatabaseError as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.refreshLayout()
