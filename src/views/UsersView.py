from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.UserCard import UserCard
from components.UserDataDialog import UserDataDialog
from database.repositories.userRepository import createUser, getAllUsers

class UsersView(QWidget):
    def __init__(self, parent=None):
        super(UsersView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(MenuButton('Crear usuario', self.create_user))

        users = getAllUsers()
        if not users:
            layout.addWidget(QLabel('There are no users'))
        for user in users:
            layout.addWidget(UserCard(user=user))
        
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    def create_user(self):
        userDialog = UserDataDialog()
        if userDialog.exec():
            name, email, password, role = userDialog.getInputs()
            createUser(name, email, password, role)