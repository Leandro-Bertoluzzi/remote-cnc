"""Application service for User domain operations."""

from collections.abc import Callable

from core.domain.entities import User
from core.ports.db_session import DbSession, SessionFactory
from core.ports.user_repository import IUserRepository


class UserService:
    """Encapsulates all user-related database operations."""

    def __init__(
        self,
        session_factory: SessionFactory,
        user_repo_factory: Callable[[DbSession], IUserRepository],
    ):
        self._session_factory = session_factory
        self._user_repo_factory = user_repo_factory

    def get_all_users(self) -> list[User]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            return repository.get_all_users()

    def get_user_by_id(self, user_id: int) -> User:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            return repository.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            return repository.get_user_by_email(email)

    def create_user(self, name: str, email: str, password: str, role: str) -> User:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            return repository.create_user(name, email, password, role)

    def update_user(self, user_id: int, name: str, email: str, role: str) -> User:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            return repository.update_user(user_id, name, email, role)

    def remove_user(self, user_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._user_repo_factory(session)
            repository.remove_user(user_id)
