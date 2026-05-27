"""Service layer for User domain operations."""

from core.domain.entities import User
from core.ports.db_session import SessionFactory

from desktop.services.dependencies import get_user_repository


class UserService:
    """Encapsulates all user-related database operations."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def get_all_users(self) -> list[User]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_user_repository(session)
            return repository.get_all_users()

    def create_user(self, name: str, email: str, password: str, role: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_user_repository(session)
            repository.create_user(name, email, password, role)

    def update_user(self, user_id: int, name: str, email: str, role: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_user_repository(session)
            repository.update_user(user_id, name, email, role)

    def remove_user(self, user_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_user_repository(session)
            repository.remove_user(user_id)
