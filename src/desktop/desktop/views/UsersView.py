from typing import TYPE_CHECKING

from desktop.components.cards.UserCard import UserCard
from desktop.components.dialogs.UserDataDialog import UserDataDialog
from desktop.services.userService import UserService
from desktop.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from MainWindow import MainWindow  # pragma: no cover


class UsersView(BaseListView):
    def __init__(self, parent: "MainWindow"):
        super(UsersView, self).__init__(parent)
        self.setItemListFromValues(
            "USUARIOS", "", self.createUserCard, "Crear usuario", self.createUser
        )
        self.refreshLayout()

    def createUserCard(self, user):
        return UserCard(user, self)

    def getItems(self):
        return UserService.get_all_users()

    def createUser(self):
        userDialog = UserDataDialog()
        if not userDialog.exec():
            return

        name, email, password, role = userDialog.getInputs()
        try:
            UserService.create_user(name, email, password, role)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()
