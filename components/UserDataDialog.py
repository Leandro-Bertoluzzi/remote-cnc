from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
from PyQt5.QtCore import Qt
from database.models.user import VALID_ROLES

class UserDataDialog(QDialog):
    def __init__(self, userInfo=None, parent=None):
        super(UserDataDialog, self).__init__(parent)

        self.name = QLineEdit(self)
        self.email = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox(self)
        self.role.addItems(VALID_ROLES)

        if userInfo:
            self.name.setText(userInfo.name)
            self.email.setText(userInfo.email)
            self.password.setEnabled(False)
            self.role.setCurrentIndex(VALID_ROLES.index(userInfo.role))

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
        self.setWindowTitle('Crear usuario' if not userInfo else 'Actualizar usuario')

    def getInputs(self):
        return (self.name.text(), self.email.text(), self.password.text(), self.role.currentText())