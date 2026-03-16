from pathlib import Path

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root (../../.. relative to this file = src/core/core -> root)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # DB connection
    db_port: str = "5432"
    db_user: str = "postgres"
    db_pass: str = ""
    db_name: str = "cnc"
    db_host: str = "localhost"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_celery: int = 0
    redis_db_storage: int = 1

    # GRBL
    grbl_simulation: bool = False

    # Serial communication
    serial_port: str = ""
    serial_baudrate: int = 115200

    # Security
    token_secret: str = ""

    # Files management
    files_folder_path: str = "/app/gcode_files"
    images_folder_path: str = "/app/thumbnails"
    logs_folder_path: str = "/app/logs"

    # Derived / computed
    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field
    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_celery}"

    @field_validator("grbl_simulation", mode="before")
    @classmethod
    def _parse_bool(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes")
        return bool(v)


# Singleton instance
settings = Settings()

# ---------------------------------------------------------------------------
# Backwards-compatible aliases so existing imports keep working.
# New code should import ``settings`` and access attributes directly.
# ---------------------------------------------------------------------------
DB_PORT = settings.db_port
DB_USER = settings.db_user
DB_PASS = settings.db_pass
DB_NAME = settings.db_name
DB_HOST = settings.db_host

REDIS_HOST = settings.redis_host
REDIS_PORT = settings.redis_port
REDIS_DB_CELERY = settings.redis_db_celery
REDIS_DB_STORAGE = settings.redis_db_storage

GRBL_SIMULATION = settings.grbl_simulation

SERIAL_PORT = settings.serial_port
SERIAL_BAUDRATE = settings.serial_baudrate

TOKEN_SECRET = settings.token_secret

FILES_FOLDER_PATH = settings.files_folder_path
IMAGES_FOLDER_PATH = settings.images_folder_path
LOGS_FOLDER_PATH = settings.logs_folder_path

SQLALCHEMY_DATABASE_URI = settings.sqlalchemy_database_uri
CELERY_BROKER_URL = CELERY_RESULT_BACKEND = settings.celery_broker_url
