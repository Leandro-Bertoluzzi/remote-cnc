from PyQt5.QtWidgets import QPushButton
from components.cards.Card import Card
from components.dialogs.UserDataDialog import UserDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.userRepository import UserRepository
from helpers.utils import needs_confirmation


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
        if not userDialog.exec():
            return

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

    @needs_confirmation('¿Realmente desea eliminar el usuario?', 'Eliminar usuario')
    def removeUser(self):
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
