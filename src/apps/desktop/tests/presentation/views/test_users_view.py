import pytest
from core.domain.entities import User
from manager.adapters.desktop.presentation.components.buttons.MenuButton import MenuButton
from manager.adapters.desktop.presentation.components.cards.UserCard import UserCard
from manager.adapters.desktop.presentation.components.ConnectionErrorWidget import (
    ConnectionErrorWidget,
)
from manager.adapters.desktop.presentation.components.dialogs.UserDataDialog import UserDataDialog
from manager.adapters.desktop.presentation.MainWindow import MainWindow
from manager.adapters.desktop.presentation.views.UsersView import UsersView
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestUsersView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_window: MainWindow):
        user_1 = User(name="John 1", email="test1@testing.com", password="1234", role="user")
        user_2 = User(name="John 2", email="test2@testing.com", password="1234", role="user")
        user_3 = User(name="John 3", email="test3@testing.com", password="1234", role="user")
        self.users_list = [user_1, user_2, user_3]

        # Configure context service mock
        mock_window._context.user_service.get_all_users.return_value = self.users_list
        self.mock_user_service = mock_window._context.user_service

        # Create an instance of UsersView
        self.parent = mock_window
        self.users_view = UsersView(self.parent)
        qtbot.addWidget(self.users_view)

        # Reset call counts accumulated during view creation
        self.mock_user_service.get_all_users.reset_mock()

    def test_users_view_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 3

    def test_users_view_init_db_error(self, helpers):
        self.mock_user_service.get_all_users.side_effect = Exception("mocked-error")
        self.mock_user_service.get_all_users.return_value = None

        # Create test view
        users_view = UsersView(self.parent)

        # Assertions
        self.mock_user_service.get_all_users.assert_called()
        assert helpers.count_widgets(users_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(users_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(users_view.layout(), UserCard) == 0

    def test_users_view_refresh_layout(self, helpers):
        # We remove a user
        self.users_list.pop()

        # Call the refreshLayout method
        self.users_view.refreshLayout()

        # Validate service calls
        assert self.mock_user_service.get_all_users.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 2

    def test_users_view_refresh_layout_db_error(self, helpers):
        self.mock_user_service.get_all_users.side_effect = Exception("mocked-error")

        self.users_view.refreshLayout()

        assert self.mock_user_service.get_all_users.call_count == 1
        assert helpers.count_widgets(self.users_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 0

    def test_users_view_create_user(self, mocker: MockerFixture, helpers):
        # Mock UserDataDialog methods
        mock_inputs = "John 4", "test4@testing.com", "1234", "user"
        mocker.patch.object(UserDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, "getInputs", return_value=mock_inputs)

        # Mock service method
        def side_effect_create_user(name, email, password, role):
            user_4 = User(name="John 4", email="test4@testing.com", password="1234", role="user")
            self.users_list.append(user_4)
            return

        self.mock_user_service.create_user.side_effect = side_effect_create_user

        # Call the createUser method
        self.users_view.createUser()

        # Validate service calls
        assert self.mock_user_service.create_user.call_count == 1
        assert self.mock_user_service.get_all_users.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 4

    def test_users_view_create_user_db_error(self, mocker: MockerFixture, helpers):
        # Mock UserDataDialog methods
        mock_inputs = "John 4", "test4@testing.com", "1234", "user"
        mocker.patch.object(UserDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(UserDataDialog, "getInputs", return_value=mock_inputs)

        # Mock service method to simulate exception
        self.mock_user_service.create_user.side_effect = Exception("mocked-error")

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        # Call the createUser method
        self.users_view.createUser()

        # Assertions
        assert self.mock_user_service.create_user.call_count == 1
        assert self.mock_user_service.get_all_users.call_count == 0
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(self.users_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.users_view.layout(), UserCard) == 3

    # Handler tests

    def test_users_view_on_user_update_success(self):
        user = self.users_list[0]
        user.id = 1
        self.users_view.on_user_update(user, "Updated Name", "updated@email.com", "admin")
        self.mock_user_service.update_user.assert_called_once_with(
            1, "Updated Name", "updated@email.com", "admin"
        )
        assert self.mock_user_service.get_all_users.call_count == 1

    def test_users_view_on_user_update_error(self, mocker: MockerFixture):
        self.mock_user_service.update_user.side_effect = Exception("e")
        mock_error = mocker.patch.object(self.users_view, "showError")
        user = self.users_list[0]
        user.id = 1
        self.users_view.on_user_update(user, "name", "email", "role")
        assert mock_error.call_count == 1
        assert self.mock_user_service.get_all_users.call_count == 0

    def test_users_view_on_user_remove_success(self):
        user = self.users_list[0]
        user.id = 1
        self.users_view.on_user_remove(user)
        self.mock_user_service.remove_user.assert_called_once_with(1)
        assert self.mock_user_service.get_all_users.call_count == 1
