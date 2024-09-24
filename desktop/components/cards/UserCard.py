from components.cards.Card import Card
from components.dialogs.UserDataDialog import UserDataDialog
from core.database.base import SessionLocal
from core.database.models import User
from core.database.repositories.userRepository import UserRepository
from helpers.utils import needs_confirmation


class UserCard(Card):
    def __init__(self, user: User, parent=None):
        super(UserCard, self).__init__(parent)

        self.user = user
        self.setup_ui()

    def setup_ui(self):
        description = f'Usuario {self.user.id}: {self.user.name}'
        self.setDescription(description)

        self.addButton("Editar", self.updateUser)
        self.addButton("Borrar", self.removeUser)

    def updateUser(self):
        userDialog = UserDataDialog(self.user)
        if not userDialog.exec():
            return

        name, email, _, role = userDialog.getInputs()
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
        self.getView().refreshLayout()

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
        self.getView().refreshLayout()
