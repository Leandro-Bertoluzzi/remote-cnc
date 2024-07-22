from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, \
    QPushButton, QFileDialog
from PyQt5.QtCore import Qt
import os


class FileDataDialog(QDialog):
    def __init__(self, fileInfo=None, parent=None):
        super(FileDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)
        self.name.setEnabled(False)
        self.file = QPushButton('Select file')
        self.file.clicked.connect(self.openFile)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttonBox.setEnabled(False)
        self.file_path = ''

        if fileInfo:
            self.name.setText(fileInfo.file_name)
            self.name.setEnabled(True)
            self.buttonBox.setEnabled(True)

        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        if not fileInfo:
            layout.addRow('Archivo', self.file)
        layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Subir archivo' if not fileInfo else 'Actualizar archivo')

    def openFile(self):
        filename, filter = QFileDialog.getOpenFileName(
            self,
            "Select a File",
            "C:\\",
            "G code files (*.txt *.gcode *.nc)"
        )
        if filename:
            self.file_path = filename
            file_name = os.path.basename(filename)

            self.name.setText(file_name)
            self.name.setEnabled(True)
            self.buttonBox.setEnabled(True)

    def getInputs(self):
        return (self.name.text(), self.file_path)
