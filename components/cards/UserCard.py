from PyQt5.QtWidgets import QPushButton, QMessageBox
from components.cards.Card import Card
from components.dialogs.UserDataDialog import UserDataDialog
from utils.database import update_user, remove_user

class UserCard(Card):
    def __init__(self, user, parent=None):
        super(UserCard, self).__init__(parent)

        self.user = user

        description = f'Usuario {user.id}: {user.name}'
        editUserBtn = QPushButton("Editar")
        editUserBtn.clicked.connect(self.updateUser)
        removeUserBtn = QPushButton("Borrar")
        removeUserBtn.clicked.connect(self.removeUser)

        self.setDescription(description)
        self.addButton(editUserBtn)
        self.addButton(removeUserBtn)

    def updateUser(self):
        userDialog = UserDataDialog(self.user)
        if userDialog.exec():
            name, email, password, role = userDialog.getInputs()
            update_user(self.user.id, name, email, role)
            self.parent().refreshLayout()

    def removeUser(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el usuario?')
        confirmation.setWindowTitle('Eliminar usuario')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            remove_user(self.user.id)
            self.parent().refreshLayout()
