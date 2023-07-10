import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from components.UserCard import UserCard
from components.UserDataDialog import UserDataDialog
from database.models.user import User
from views.UsersView import UsersView

class TestUserCard:
    user = User(name='John Doe', email='test@testing.com', password='1234', role='user')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(UsersView, 'refreshLayout')

        self.parent = UsersView()
        self.card = UserCard(self.user, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_user_card_init(self, qtbot):
        assert self.card.user == self.user
        assert self.card.layout() is not None

    def test_user_card_update_user(self, qtbot, mocker):
        # Mock UserDataDialog methods
        mock_input = 'Updated Name', 'updated@email.com', 'updatedpassword', 'admin'
        mocker.patch.object(UserDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_user = mocker.patch('components.UserCard.updateUser')

        # Call the updateUser method
        self.card.updateUser()

        # Validate DB calls
        mock_update_user.call_count == 1

    def test_user_card_remove_user(self, qtbot, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_user = mocker.patch('components.UserCard.removeUser')

        # Call the removeUser method
        self.card.removeUser()

        # Validate DB calls
        mock_remove_user.call_count == 1
