from unittest.mock import MagicMock

from desktop.services.userService import UserService
from pytest_mock.plugin import MockerFixture


class TestUserService:
    @staticmethod
    def _make_service_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        mocker.patch(
            "desktop.services.userService.get_user_repository",
            return_value=repository,
        )
        service = UserService(session_factory=session_factory)
        return service, session, repository

    def test_create_user(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        result = service.create_user("User", "user@email.com", "pass", "admin")

        repository.create_user.assert_called_once_with("User", "user@email.com", "pass", "admin")
        assert result is None

    def test_get_all_users(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_users.return_value = expected

        result = service.get_all_users()

        assert result == expected
        repository.get_all_users.assert_called_once_with()

    def test_update_user(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        result = service.update_user(7, "New", "new@email.com", "operator")

        repository.update_user.assert_called_once_with(7, "New", "new@email.com", "operator")
        assert result is None

    def test_remove_user(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        result = service.remove_user(user_id=7)

        repository.remove_user.assert_called_once_with(7)
        assert result is None
