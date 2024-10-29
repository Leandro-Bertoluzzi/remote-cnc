from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.UserCard import UserCard
from desktop.components.dialogs.UserDataDialog import UserDataDialog
from database.models import User
from database.repositories.userRepository import UserRepository
from desktop.MainWindow import MainWindow
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from desktop.views.UsersView import UsersView


class TestUsersView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        user_1 = User(name='John 1', email='test1@testing.com', password='1234', role='user')
        user_2 = User(name='John 2', email='test2@testing.com', password='1234', role='user')
        user_3 = User(name='John 3', email='test3@testing.com', password='1234', role='user')
        self.users_list = [user_1, user_2, user_3]

        # Patch the getAllUsers method with the mock function
        self.mock_get_all_users = mocker.patch.object(
            UserRepository,
            'get_all_users',
            return_value=self.users_list
        )

        # Create an instance of UsersView
        self.parent = mock_window
        self.users_view = UsersView(self.parent)
        qtbot.addWidget(self.users_view)

    def test_users_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_users.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 3

    def test_users_view_init_db_error(self, mocker: MockerFixture, helpers):
        mock_get_all_users = mocker.patch.object(
            UserRepository,
            'get_all_users',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Create test view
        users_view = UsersView(self.parent)

        # Assertions
        mock_get_all_users.assert_called_once()
        mock_popup.assert_called_once()
        assert helpers.count_widgets(users_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(users_view.layout(), UserCard) == 0

    def test_users_view_refresh_layout(self, helpers):
        # We remove a user
        self.users_list.pop()

        # Call the refreshLayout method
        self.users_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_users.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 2

    def test_users_view_refresh_layout_db_error(self, mocker: MockerFixture, helpers):
        # Mock DB methods to simulate error(s)
        # 1st execution: Widget creation (needs to success)
        # 2nd execution: Test case
        mock_get_all_users = mocker.patch.object(
            UserRepository,
            'get_all_users',
            side_effect=[
                self.users_list,
                Exception('mocked-error')
            ]
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the method under test
        users_view = UsersView(self.parent)
        users_view.refreshLayout()

        # Assertions
        assert mock_get_all_users.call_count == 2
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(users_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(users_view.layout(), UserCard) == 0

    def test_users_view_create_user(self, mocker: MockerFixture, helpers):
        # Mock UserDataDialog methods
        mock_inputs = 'John 4', 'test4@testing.com', '1234', 'user'
        mocker.patch.object(UserDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_user(name, email, password, role):
            user_4 = User(
                name='John 4',
                email='test4@testing.com',
                password='1234',
                role='user'
            )
            self.users_list.append(user_4)
            return

        mock_create_user = mocker.patch.object(
            UserRepository,
            'create_user',
            side_effect=side_effect_create_user
        )

        # Call the createUser method
        self.users_view.createUser()

        # Validate DB calls
        assert mock_create_user.call_count == 1
        assert self.mock_get_all_users.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 4

    def test_users_view_create_user_db_error(self, mocker: MockerFixture, helpers):
        # Mock UserDataDialog methods
        mock_inputs = 'John 4', 'test4@testing.com', '1234', 'user'
        mocker.patch.object(UserDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method to simulate exception
        mock_create_user = mocker.patch.object(
            UserRepository,
            'create_user',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the createUser method
        self.users_view.createUser()

        # Assertions
        assert mock_create_user.call_count == 1
        assert self.mock_get_all_users.call_count == 1
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 3
