from PyQt5.QtWidgets import QPushButton, QMessageBox
from components.cards.Card import Card
from components.dialogs.UserDataDialog import UserDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.userRepository import UserRepository


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
            try:
                db_session = SessionLocal()
                repository = UserRepository(db_session)
                repository.update_user(self.user.id, name, email, role)
            except Exception as error:
                self.showError(
                    'Error de base de datos',
                    str(error)
                )
                return
            self.parent().refreshLayout()

    def removeUser(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el usuario?')
        confirmation.setWindowTitle('Eliminar usuario')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            try:
                db_session = SessionLocal()
                repository = UserRepository(db_session)
                repository.remove_user(self.user.id)
            except Exception as error:
                self.showError(
                    'Error de base de datos',
                    str(error)
                )
                return
            self.parent().refreshLayout()
