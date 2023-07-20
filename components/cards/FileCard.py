from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.dialogs.FileDataDialog import FileDataDialog
from database.repositories.fileRepository import updateFile, removeFile
from utils.files import renameFile, deleteFile

class FileCard(QWidget):
    def __init__(self, file, parent=None):
        super(FileCard, self).__init__(parent)

        self.file = file

        fileDescription = QLabel(f'Archivo {file.id}: {file.file_name}')
        editFileBtn = QPushButton("Editar")
        editFileBtn.clicked.connect(self.updateFile)
        removeFileBtn = QPushButton("Borrar")
        removeFileBtn.clicked.connect(self.removeFile)

        layout = QHBoxLayout()
        layout.addWidget(fileDescription)
        layout.addWidget(editFileBtn)
        layout.addWidget(removeFileBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def updateFile(self):
        fileDialog = FileDataDialog(self.file)
        if fileDialog.exec():
            name, path = fileDialog.getInputs()

            # Update file in the file system
            try:
                generatedFilename = renameFile(self.file.user_id, self.file.file_path, name)
            except Exception as error:
                print('Error: ', error)

            # Update the entry for the file in the DB
            try:
                updateFile(self.file.id, self.file.user_id, name, generatedFilename)
            except Exception as error:
                print('Error: ', error)

            self.parent().refreshLayout()

    def removeFile(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el archivo?')
        confirmation.setWindowTitle('Eliminar archivo')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            # Remove the file from the file system
            try:
                deleteFile(self.file.file_path)
            except Exception as error:
                print('Error: ', error)

            # Remove the entry for the file in the DB
            try:
                removeFile(self.file.id)
            except Exception as error:
                print('Error: ', error)

            self.parent().refreshLayout()
