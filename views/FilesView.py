from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.cards.FileCard import FileCard
from components.cards.MsgCard import MsgCard
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import DuplicatedFileError, \
    DuplicatedFileNameError, FileRepository
from core.utils.files import computeSHA256, copyFile


class FilesView(QWidget):
    def __init__(self, parent=None):
        super(FilesView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createFile(self):
        fileDialog = FileDataDialog()
        if fileDialog.exec():
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

    def showWarning(self, title, text):
        QMessageBox.warning(self, title, text, QMessageBox.Ok)

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            db_session = SessionLocal()
            repository = FileRepository(db_session)
            files = repository.get_all_files()
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error de base de datos',
                str(error),
                QMessageBox.Ok
            )
            return

        self.layout.addWidget(MenuButton('Subir archivo', self.createFile))

        for file in files:
            self.layout.addWidget(FileCard(file, self))

        if not files:
            self.layout.addWidget(MsgCard('Aún no hay archivos almacenados', self))

        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()
