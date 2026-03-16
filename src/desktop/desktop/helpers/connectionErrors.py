"""Utilities for classifying and handling external service connection errors.

Provides human-readable error messages in Spanish for connection failures
to PostgreSQL, Redis, and Celery/broker services.
"""

import logging

logger = logging.getLogger(__name__)

# Human-readable error messages
DB_CONNECTION_ERROR = (
    "No se pudo conectar a la base de datos.\n"
    "Verifique que el servidor PostgreSQL esté en ejecución."
)
REDIS_CONNECTION_ERROR = (
    "No se pudo conectar al servidor de tareas.\nVerifique que el servicio Redis esté en ejecución."
)
WORKER_CONNECTION_ERROR = (
    "No se pudo comunicar con el worker de tareas.\n"
    "Verifique que Redis y el worker estén en ejecución."
)


def classify_connection_error(exc: BaseException) -> str | None:
    """Inspect an exception (and its __cause__ chain) to determine if it is
    a connection error to an external service.

    Returns a human-readable message string if the error is a known connection
    issue, or ``None`` if it is not.
    """
    current: BaseException | None = exc
    while current is not None:
        type_name = type(current).__name__
        module = type(current).__module__ or ""

        # PostgreSQL / SQLAlchemy connection errors
        if type_name == "OperationalError" and ("psycopg2" in module or "sqlalchemy" in module):
            return DB_CONNECTION_ERROR

        # Redis connection errors
        if "redis" in module and "ConnectionError" in type_name:
            return REDIS_CONNECTION_ERROR

        # Kombu / Celery broker errors
        if "kombu" in module and "OperationalError" in type_name:
            return WORKER_CONNECTION_ERROR

        # Celery inspect timeout (returns None from ping)
        if "celery" in module and "OperationalError" in type_name:
            return WORKER_CONNECTION_ERROR

        current = getattr(current, "__cause__", None)

    return None


def get_friendly_error_message(exc: BaseException) -> str:
    """Return a friendly error message for the exception.

    If it is a known connection error, returns the appropriate friendly
    message. Otherwise returns ``str(exc)``.
    """
    friendly = classify_connection_error(exc)
    return friendly if friendly is not None else str(exc)
