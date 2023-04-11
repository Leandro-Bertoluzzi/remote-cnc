from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.UserDataDialog import UserDataDialog
from database.repositories.userRepository import updateUser, removeUser

class UserCard(QWidget):
    def __init__(self, user, parent=None):
        super(UserCard, self).__init__(parent)

        self.user = user

        userDescription = QLabel(f'User {user.id}: {user.name}')
        editUserBtn = QPushButton("Editar")
        editUserBtn.clicked.connect(self.updateUser)
        removeUserBtn = QPushButton("Borrar")
        removeUserBtn.clicked.connect(self.removeUser)

        layout = QHBoxLayout()
        layout.addWidget(userDescription)
        layout.addWidget(editUserBtn)
        layout.addWidget(removeUserBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "UserCard.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())
    
    def updateUser(self):
        userDialog = UserDataDialog(self.user)
        if userDialog.exec():
            name, email, password, role = userDialog.getInputs()
            updateUser(self.user.id, name, email, password, role)
            self.parent().refreshLayout()
    
    def removeUser(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el usuario?')
        confirmation.setWindowTitle('Eliminar usuario')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            removeUser(self.user.id)
            self.parent().refreshLayout()