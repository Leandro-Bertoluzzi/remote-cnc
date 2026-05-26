"""Database session management for the desktop application."""

from contextlib import contextmanager
from typing import Callable

from core.adapters.database.base import SessionLocal
from core.ports.db_session import DbSession

# Module-level session factory. Defaults to the production SQLAlchemy
# factory; replaced at startup by configure_session_factory() so that
# tests and alternative environments can supply a different session.
_session_factory: Callable[..., DbSession] = SessionLocal


def configure_session_factory(factory: Callable[..., DbSession]) -> None:
    """Replace the module-level session factory.

    Must be called from the composition root (``desktop/main.py``) before
    any service method that uses ``get_db_session()`` is invoked.
    """
    global _session_factory  # noqa: PLW0603
    _session_factory = factory


@contextmanager
def get_db_session():
    """Context manager that yields a DB session and ensures it is closed.

    Usage::

        with get_db_session() as session:
            repo = SomeRepository(session)
            repo.do_something()
    """
    session = _session_factory(expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
