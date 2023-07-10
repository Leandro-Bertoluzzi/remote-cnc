import pytest
from components.UserDataDialog import UserDataDialog
from database.models.user import User, VALID_ROLES

class TestUserDataDialog:
    userInfo = User(name='John Doe', email='test@testing.com', password='1234', role='admin')

    def test_user_data_dialog_init(self, qtbot):
        dialog = UserDataDialog()
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("user_info", [None, userInfo])
    def test_user_data_dialog_init_widgets(self, qtbot, user_info):
        dialog = UserDataDialog(userInfo=user_info)
        qtbot.addWidget(dialog)

        expectedName = self.userInfo.name if user_info is not None else ''
        expectedEmail = self.userInfo.email if user_info is not None else ''
        expectedPasswordEnabled = False if user_info is not None else True
        expectedRoleIndex = VALID_ROLES.index(self.userInfo.role) if user_info is not None else 0
        expectedWindowTitle = 'Actualizar usuario' if user_info is not None else 'Crear usuario'

        assert dialog.name.text() == expectedName
        assert dialog.email.text() == expectedEmail
        assert dialog.password.isEnabled() == expectedPasswordEnabled
        assert dialog.role.currentIndex() == expectedRoleIndex
        assert dialog.windowTitle() == expectedWindowTitle

    def test_user_data_dialog_get_inputs(self, qtbot):
        dialog = UserDataDialog(userInfo=self.userInfo)
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('Updated Name')
        dialog.email.setText('updated@testing.com')
        dialog.role.setCurrentIndex(VALID_ROLES.index('user'))

        assert dialog.getInputs() == ('Updated Name', 'updated@testing.com', '', 'user')
