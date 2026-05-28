import pytest
from core.domain.entities import User
from desktop.components.cards.UserCard import UserCard
from desktop.components.dialogs.UserDataDialog import UserDataDialog
from PyQt5.QtWidgets import QDialog, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestUserCard:
    user = User(name="John Doe", email="test@testing.com", password="1234", role="user")

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        self.user.id = 1
        self.parent = mock_view
        self.card = UserCard(self.user, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_user_card_init(self):
        assert self.card.user == self.user
        assert self.card.layout is not None

    @pytest.mark.parametrize(
        "dialogResponse,expected_emitted", [(QDialog.Accepted, True), (QDialog.Rejected, False)]
    )
    def test_user_card_update_user(self, mocker: MockerFixture, dialogResponse, expected_emitted):
        mock_input = "Updated Name", "updated@email.com", "updatedpassword", "admin"
        mocker.patch.object(UserDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(UserDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.update_requested.connect(handler)

        self.card.updateUser()

        if expected_emitted:
            handler.assert_called_once_with(self.user, "Updated Name", "updated@email.com", "admin")
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize(
        "msgBoxResponse,expected_emitted", [(QMessageBox.Yes, True), (QMessageBox.Cancel, False)]
    )
    def test_user_card_remove_user(self, mocker: MockerFixture, msgBoxResponse, expected_emitted):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.remove_requested.connect(handler)

        self.card.removeUser()

        if expected_emitted:
            handler.assert_called_once_with(self.user)
        else:
            handler.assert_not_called()
