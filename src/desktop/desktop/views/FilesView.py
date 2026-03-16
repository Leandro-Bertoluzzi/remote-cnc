from typing import TYPE_CHECKING

from core.database.exceptions import DatabaseError
from core.database.repositories.fileRepository import DuplicatedFileError, DuplicatedFileNameError
from core.utilities.files import FileSystemError, InvalidFile

from desktop.components.cards.FileCard import FileCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.config import USER_ID
from desktop.services.fileService import FileService
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
        return FileService.get_all_files()

    def createFile(self):
        fileDialog = FileDataDialog()
        if not fileDialog.exec():
            return

        name, path = fileDialog.getInputs()

        try:
            FileService.create_file(USER_ID, name, path)
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
