from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.UserDataDialog import UserDataDialog
from database.repositories.userRepository import updateUser

class UserCard(QWidget):
    def __init__(self, user, parent=None):
        super(UserCard, self).__init__(parent)

        self.user = user

        userDescription = QLabel(f'User {user.id}: {user.name}')
        editUserBtn = QPushButton("A")
        editUserBtn.clicked.connect(self.updateUser)

        layout = QHBoxLayout()
        layout.addWidget(userDescription)
        layout.addWidget(editUserBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "UserCard.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())
    
    def updateUser(self):
        userDialog = UserDataDialog(self.user)
        if userDialog.exec():
            name, email, password, role = userDialog.getInputs()
            updateUser(self.user.id, name, email, password, role)