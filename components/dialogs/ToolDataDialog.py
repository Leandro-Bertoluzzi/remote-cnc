from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, QTextEdit
from PyQt5.QtCore import Qt

class ToolDataDialog(QDialog):
    def __init__(self, toolInfo=None, parent=None):
        super(ToolDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)
        self.description = QTextEdit(self)

        if toolInfo:
            self.name.setText(toolInfo.name)
            self.description.setPlainText(toolInfo.description)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        layout.addRow('Descripción (opcional)', self.description)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Agregar herramienta' if not toolInfo else 'Actualizar herramienta')

    def getInputs(self):
        return (self.name.text(), self.description.toPlainText())
