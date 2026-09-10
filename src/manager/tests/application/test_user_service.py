from unittest.mock import MagicMock

from manager.application.user_service import UserService


class TestUserService:
    @staticmethod
    def _make_service_and_repo():
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        service = UserService(
            session_factory=session_factory,
            user_repo_factory=MagicMock(return_value=repository),
        )
        return service, repository

    def test_create_user(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.create_user.return_value = expected

        result = service.create_user("User", "user@email.com", "pass", "admin")

        repository.create_user.assert_called_once_with("User", "user@email.com", "pass", "admin")
        assert result == expected

    def test_get_user_by_id(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.get_user_by_id.return_value = expected

        result = service.get_user_by_id(7)

        assert result == expected
        repository.get_user_by_id.assert_called_once_with(7)

    def test_get_user_by_email(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.get_user_by_email.return_value = expected

        result = service.get_user_by_email("user@email.com")

        assert result == expected
        repository.get_user_by_email.assert_called_once_with("user@email.com")

    def test_get_all_users(self):
        service, repository = self._make_service_and_repo()
        expected = [MagicMock(), MagicMock()]
        repository.get_all_users.return_value = expected

        result = service.get_all_users()

        assert result == expected
        repository.get_all_users.assert_called_once_with()

    def test_update_user(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.update_user.return_value = expected

        result = service.update_user(7, "New", "new@email.com", "operator")

        repository.update_user.assert_called_once_with(7, "New", "new@email.com", "operator")
        assert result == expected

    def test_remove_user(self):
        service, repository = self._make_service_and_repo()

        result = service.remove_user(user_id=7)

        repository.remove_user.assert_called_once_with(7)
        assert result is None
