"""Database session management for the desktop application."""

from contextlib import contextmanager

from core.database.base import SessionLocal


@contextmanager
def get_db_session():
    """Context manager that yields a SQLAlchemy session and ensures it is
    closed after use, even if an exception occurs.

    Usage::

        with get_db_session() as session:
            repo = SomeRepository(session)
            repo.do_something()
    """
    session = SessionLocal(expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
