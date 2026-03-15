from typing import TYPE_CHECKING

from core.database.base import SessionLocal
from core.database.repositories.fileRepository import (
    DatabaseError,
    DuplicatedFileError,
    DuplicatedFileNameError,
    FileRepository,
)
from core.utilities.fileManager import FileManager
from core.utilities.files import FileSystemError, InvalidFile
from core.utilities.worker.scheduler import create_thumbnail, generate_file_report

from desktop.components.cards.FileCard import FileCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.config import FILES_FOLDER_PATH, USER_ID
from desktop.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from MainWindow import MainWindow  # pragma: no cover


class FilesView(BaseListView):
    def __init__(self, parent: "MainWindow"):
        super(FilesView, self).__init__(parent)
        self.setItemListFromValues(
            "ARCHIVOS",
            "Aún no hay archivos almacenados",
            self.createFileCard,
            "Subir archivo",
            self.createFile,
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

        db_session = SessionLocal()
        file_manager = FileManager(FILES_FOLDER_PATH, db_session)
        try:
            file = file_manager.create_file(USER_ID, name, path)
            generate_file_report(file.id)
            create_thumbnail(file.id)
        except (DuplicatedFileNameError, DuplicatedFileError) as error:
            self.showWarning("Archivo repetido", str(error))
            return
        except (InvalidFile, FileSystemError) as error:
            self.showError("Error de guardado", str(error))
            return
        except DatabaseError as error:
            self.showError("Error de base de datos", str(error))
            return

        self.refreshLayout()
