from core.config import SQLALCHEMY_DATABASE_URI
from core.ports.db_session import SessionFactory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal: SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)  # type: ignore[assignment]


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""

    pass


def check_db_connection() -> None:
    """Verify that the database is reachable by executing a trivial query.

    Raises ``sqlalchemy.exc.SQLAlchemyError`` (or any underlying DB driver
    exception) if the connection cannot be established.

    Intended for use in application startup health-checks.  Callers should
    never import ``engine`` directly for this purpose.
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def dispose_db() -> None:
    """Release all pooled database connections.

    Call during application shutdown to allow clean process exit.
    """
    engine.dispose()
