from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, QTextEdit
from PyQt5.QtCore import Qt

class MaterialDataDialog(QDialog):
    def __init__(self, materialInfo=None, parent=None):
        super(MaterialDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)
        self.description = QTextEdit(self)

        if materialInfo:
            self.name.setText(materialInfo.name)
            self.description.setPlainText(materialInfo.description)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        layout.addRow('Descripción (opcional)', self.description)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Agregar material' if not materialInfo else 'Actualizar material')

    def getInputs(self):
        return (self.name.text(), self.description.toPlainText())
