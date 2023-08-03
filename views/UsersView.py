from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.cards.UserCard import UserCard
from components.dialogs.UserDataDialog import UserDataDialog
from utils.database import create_user, get_all_users

class UsersView(QWidget):
    def __init__(self, parent=None):
        super(UsersView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createUser(self):
        userDialog = UserDataDialog()
        if userDialog.exec():
            name, email, password, role = userDialog.getInputs()
            create_user(name, email, password, role)
            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(MenuButton('Crear usuario', self.createUser))

        users = get_all_users()
        for user in users:
            self.layout.addWidget(UserCard(user, self))
        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()
