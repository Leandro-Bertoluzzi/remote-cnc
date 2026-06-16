from typing import TYPE_CHECKING

from desktop.presentation.components.cards.UserCard import UserCard
from desktop.presentation.components.dialogs.UserDataDialog import UserDataDialog
from desktop.presentation.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from desktop.presentation.MainWindow import MainWindow  # pragma: no cover


class UsersView(BaseListView):
    def __init__(self, parent: "MainWindow", **kwargs):
        super(UsersView, self).__init__(parent, **kwargs)
        self.setItemListFromValues(
            "USUARIOS", "", self.createUserCard, "Crear usuario", self.createUser
        )
        self.refreshLayout()

    def createUserCard(self, user):
        card = UserCard(user, self)
        card.update_requested.connect(self.on_user_update)
        card.remove_requested.connect(self.on_user_remove)
        return card

    def getItems(self):
        return self._context.user_service.get_all_users()

    def createUser(self):
        userDialog = UserDataDialog()
        if not userDialog.exec():
            return

        name, email, password, role = userDialog.getInputs()
        try:
            self._context.user_service.create_user(name, email, password, role)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    # Signal handlers

    def on_user_update(self, user, name, email, role):
        if user.id is None:
            return

        try:
            self._context.user_service.update_user(user.id, name, email, role)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    def on_user_remove(self, user):
        if user.id is None:
            return

        try:
            self._context.user_service.remove_user(user.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()
