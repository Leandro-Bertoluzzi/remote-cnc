from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.dialogs.FileDataDialog import FileDataDialog
from database.repositories.fileRepository import updateFile, removeFile

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
            name = fileDialog.getInputs()
            updateFile(self.file.id, self.file.user_id, name, name)
            self.parent().refreshLayout()

    def removeFile(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el archivo?')
        confirmation.setWindowTitle('Eliminar archivo')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            removeFile(self.file.id)
            self.parent().refreshLayout()
