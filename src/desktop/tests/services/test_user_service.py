from unittest.mock import MagicMock

from desktop.services.userService import UserService
from pytest_mock.plugin import MockerFixture


class TestUserService:
    @staticmethod
    def _mock_db_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.userService.get_db_session", return_value=session_ctx)
        repository = MagicMock()
        get_repo = mocker.patch(
            "desktop.services.userService.get_user_repository",
            return_value=repository,
        )
        return session, repository, get_repo

    def test_create_user(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        result = UserService.create_user("User", "user@email.com", "pass", "admin")

        get_repo.assert_called_once_with(session)
        repository.create_user.assert_called_once_with("User", "user@email.com", "pass", "admin")
        assert result is None

    def test_get_all_users(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_users.return_value = expected

        result = UserService.get_all_users()

        assert result == expected
        get_repo.assert_called_once_with(session)
        repository.get_all_users.assert_called_once_with()

    def test_update_user(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        result = UserService.update_user(7, "New", "new@email.com", "operator")

        get_repo.assert_called_once_with(session)
        repository.update_user.assert_called_once_with(7, "New", "new@email.com", "operator")
        assert result is None

    def test_remove_user(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        result = UserService.remove_user(user_id=7)

        get_repo.assert_called_once_with(session)
        repository.remove_user.assert_called_once_with(7)
        assert result is None
