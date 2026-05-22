"""Port for user persistence operations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.database.models import User


@runtime_checkable
class IUserRepository(Protocol):
    def create_user(self, name: str, email: str, password: str, role: str) -> User: ...

    def get_user_by_id(self, id: int) -> User: ...

    def get_user_by_email(self, email: str) -> User | None: ...

    def get_all_users(self) -> list[User]: ...

    def update_user(self, id: int, name: str, email: str, role: str) -> User: ...

    def remove_user(self, id: int) -> None: ...
