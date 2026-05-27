"""Port for the database session."""

from __future__ import annotations

from typing import Any, Callable, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class DbSession(Protocol):
    """Minimal structural interface expected from a DB session."""

    def get(self, entity: type[T], ident: Any) -> T | None: ...

    def scalars(self, statement: Any, /, *args: Any, **kwargs: Any) -> Any: ...

    def execute(self, statement: Any, /, *args: Any, **kwargs: Any) -> Any: ...

    def add(self, instance: Any) -> None: ...

    def delete(self, instance: Any) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def refresh(self, instance: Any) -> None: ...

    def close(self) -> None: ...


# Custom types
SessionFactory = Callable[..., DbSession]
