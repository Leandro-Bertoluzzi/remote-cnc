from core.domain.entities import User
from desktop.components.cards.Card import Card
from desktop.components.dialogs.UserDataDialog import UserDataDialog
from desktop.components.utils import needs_confirmation
from PyQt5.QtCore import pyqtSignal


class UserCard(Card):
    """Presentation-only card for a User entity."""

    # (user, name, email, role)
    update_requested = pyqtSignal(object, str, str, str)
    # (user,)
    remove_requested = pyqtSignal(object)

    def __init__(self, user: User, parent=None):
        super(UserCard, self).__init__(parent)

        self.user = user
        self.setup_ui()

    def setup_ui(self):
        description = f"Usuario {self.user.id}: {self.user.name}"
        self.setDescription(description)

        self.addButton("Editar", self.updateUser)
        self.addButton("Borrar", self.removeUser)

    def updateUser(self):
        userDialog = UserDataDialog(self.user)
        if not userDialog.exec():
            return

        name, email, _, role = userDialog.getInputs()
        self.update_requested.emit(self.user, name, email, role)

    @needs_confirmation("¿Realmente desea eliminar el usuario?", "Eliminar usuario")
    def removeUser(self):
        self.remove_requested.emit(self.user)
