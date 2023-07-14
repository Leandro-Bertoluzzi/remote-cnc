from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
from PyQt5.QtCore import Qt

class FileDataDialog(QDialog):
    def __init__(self, fileInfo=None, parent=None):
        super(FileDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)

        if fileInfo:
            self.name.setText(fileInfo.file_name)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Subir archivo' if not fileInfo else 'Actualizar archivo')

    def getInputs(self):
        return self.name.text()
