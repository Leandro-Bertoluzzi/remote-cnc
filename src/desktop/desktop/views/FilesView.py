from typing import TYPE_CHECKING

from core.domain.exceptions import (
    DuplicatedFileError,
    DuplicatedFileNameError,
    PersistenceError,
)
from core.utilities.files import FileSystemError, InvalidFile

from desktop.components.cards.FileCard import FileCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.config import USER_ID
from desktop.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from desktop.MainWindow import MainWindow  # pragma: no cover


class FilesView(BaseListView):
    def __init__(self, parent: "MainWindow", **kwargs):
        super(FilesView, self).__init__(parent, **kwargs)
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
        return self._context.file_service.get_all_files()

    def createFile(self):
        fileDialog = FileDataDialog()
        if not fileDialog.exec():
            return

        name, path = fileDialog.getInputs()

        try:
            self._context.file_service.create_file(USER_ID, name, path)
        except (DuplicatedFileNameError, DuplicatedFileError) as error:
            self.showWarning("Archivo repetido", str(error))
            return
        except (InvalidFile, FileSystemError) as error:
            self.showError("Error de guardado", str(error))
            return
        except PersistenceError as error:
            self.showError("Error de base de datos", str(error))
            return

        self.refreshLayout()
