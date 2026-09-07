from typing import TYPE_CHECKING

from core.domain.exceptions import (
    DuplicatedFileError,
    DuplicatedFileNameError,
    EntityNotFoundError,
    FileStorageError,
    InvalidFile,
    PersistenceError,
)
from manager.adapters.desktop.application.connectionErrors import get_friendly_error_message
from manager.adapters.desktop.presentation.components.cards.FileCard import FileCard
from manager.adapters.desktop.presentation.components.dialogs.FileDataDialog import FileDataDialog
from manager.adapters.desktop.presentation.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from manager.adapters.desktop.presentation.MainWindow import MainWindow  # pragma: no cover


class FilesView(BaseListView):
    def __init__(self, parent: "MainWindow", **kwargs):
        super().__init__(parent, **kwargs)

        self._user_id = self._context.settings_reader.user_id
        self.tools = []
        self.materials = []
        self.setItemListFromValues(
            "ARCHIVOS",
            "Aún no hay archivos almacenados",
            self.createFileCard,
            "Subir archivo",
            self.createFile,
        )
        self.refreshLayout()

    def createFileCard(self, item):
        card = FileCard(item, self.tools, self.materials, self)
        card.rename_requested.connect(self.on_file_rename)
        card.remove_requested.connect(self.on_file_remove)
        card.create_task_requested.connect(self.on_create_task)
        card.execute_task_requested.connect(self.on_execute_task)
        return card

    def getItems(self):
        files = self._context.file_service.get_all_files()
        _, materials, tools = self._context.asset_service.get_assets(self._user_id)
        self.tools = tools
        self.materials = materials
        return files

    # Signal handlers

    def on_file_rename(self, file, new_name):
        try:
            self._context.file_service.rename_file(self._user_id, file, new_name)
        except DuplicatedFileNameError as error:
            self.showWarning("Nombre repetido", str(error))
        except (InvalidFile, FileStorageError) as error:
            self.showError("Error de guardado", str(error))
        except (PersistenceError, EntityNotFoundError) as error:
            self.showError("Error de base de datos", str(error))
        else:
            self.refreshLayout()

    def on_file_remove(self, file):
        try:
            self._context.file_service.remove_file(file)
        except FileStorageError as error:
            self.showError("Error de borrado", str(error))
        except (PersistenceError, EntityNotFoundError) as error:
            self.showError("Error de base de datos", str(error))
        else:
            self.refreshLayout()

    def on_create_task(self, file, tool_id, material_id, name, note):
        if file.id is None:
            return

        try:
            self._context.task_service.create_task(
                self._user_id, file.id, tool_id, material_id, name, note
            )
        except Exception as error:
            self.showError("Error de base de datos", str(error))

    def on_execute_task(self, file, tool_id, material_id, name, note):
        try:
            unavailable_reason = self._context.device_service.check_device_availability()
        except Exception as error:
            self.showError("Error de conexión", get_friendly_error_message(error))
            return

        if unavailable_reason:
            self.showError("No disponible", unavailable_reason)
            return

        if file.id is None:
            return

        try:
            self._context.task_service.create_and_execute_task(
                self._user_id, file.id, tool_id, material_id, name, note
            )
        except Exception as error:
            self.showError("Error", str(error))
            return

        self.task_dispatched.emit()
        self.showInfo("Tarea enviada", "Se envió la tarea al equipo para su ejecución")

    def createFile(self):
        fileDialog = FileDataDialog()
        if not fileDialog.exec():
            return

        name, path = fileDialog.getInputs()

        try:
            self._context.file_service.create_file(self._user_id, name, path)
        except (DuplicatedFileNameError, DuplicatedFileError) as error:
            self.showWarning("Archivo repetido", str(error))
            return
        except (InvalidFile, FileStorageError) as error:
            self.showError("Error de guardado", str(error))
            return
        except PersistenceError as error:
            self.showError("Error de base de datos", str(error))
            return

        self.refreshLayout()
