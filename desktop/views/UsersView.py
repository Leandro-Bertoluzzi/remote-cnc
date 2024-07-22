from components.cards.UserCard import UserCard
from components.dialogs.UserDataDialog import UserDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.userRepository import UserRepository
from views.BaseListView import BaseListView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class UsersView(BaseListView):
    def __init__(self, parent: 'MainWindow'):
        super(UsersView, self).__init__(parent)
        self.setItemListFromValues(
            'USUARIOS',
            '',
            self.createUserCard,
            'Crear usuario',
            self.createUser
        )
        self.refreshLayout()

    def createUserCard(self, user):
        return UserCard(user, self)

    def getItems(self):
        db_session = SessionLocal()
        repository = UserRepository(db_session)
        return repository.get_all_users()

    def createUser(self):
        userDialog = UserDataDialog()
        if not userDialog.exec():
            return

        name, email, password, role = userDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = UserRepository(db_session)
            repository.create_user(name, email, password, role)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.refreshLayout()
