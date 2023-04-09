from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder

class UserCard(QWidget):
    def __init__(self, user, parent=None):
        super(UserCard, self).__init__(parent)

        userDescription = QLabel(f'User {user.id}: {user.name}')

        layout = QVBoxLayout()
        layout.addWidget(userDescription)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "UserCard.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())