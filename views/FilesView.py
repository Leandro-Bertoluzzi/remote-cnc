from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.cards.FileCard import FileCard
from components.dialogs.FileDataDialog import FileDataDialog
from config import USER_ID
from database.repositories.fileRepository import createFile, getAllFilesFromUser
from utils.files import saveFile

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

            # Save file in the file system
            try:
                generatedName = saveFile(USER_ID, path, name)
            except Exception as error:
                print('Error: ', error)

            # Create an entry for the file in the DB
            try:
                createFile(USER_ID, name, generatedName)
            except Exception as error:
                print('Error: ', error)

            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(MenuButton('Subir archivo', self.createFile))

        files = getAllFilesFromUser(USER_ID)
        for file in files:
            self.layout.addWidget(FileCard(file, self))
        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()