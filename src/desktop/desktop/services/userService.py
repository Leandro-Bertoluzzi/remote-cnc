"""Service layer for User domain operations."""

from core.database.models import User

from desktop.services import get_db_session
from desktop.services.dependencies import get_user_repository


class UserService:
    """Encapsulates all user-related database operations."""

    @classmethod
    def get_all_users(cls) -> list[User]:
        with get_db_session() as session:
            repository = get_user_repository(session)
            return repository.get_all_users()

    @classmethod
    def create_user(cls, name: str, email: str, password: str, role: str) -> None:
        with get_db_session() as session:
            repository = get_user_repository(session)
            repository.create_user(name, email, password, role)

    @classmethod
    def update_user(cls, user_id: int, name: str, email: str, role: str) -> None:
        with get_db_session() as session:
            repository = get_user_repository(session)
            repository.update_user(user_id, name, email, role)

    @classmethod
    def remove_user(cls, user_id: int) -> None:
        with get_db_session() as session:
            repository = get_user_repository(session)
            repository.remove_user(user_id)
