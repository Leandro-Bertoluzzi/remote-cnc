from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
from PyQt5.QtCore import Qt

class UserDataDialog(QDialog):
    def __init__(self, parent=None):
        super(UserDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)
        self.email = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox(self)
        self.role.addItems(['user', 'admin'])

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        
        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        layout.addRow('Correo electrónico', self.email)
        layout.addRow('Contraseña', self.password)
        layout.addRow('Rol', self.role)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
    
    def getInputs(self):
        return (self.name.text(), self.email.text(), self.password.text(), self.role.currentText())