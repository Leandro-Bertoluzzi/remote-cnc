"""Desktop application configuration.

There are two distinct layers of configuration:

**Static settings** (read once at startup):
    Managed by ``DesktopSettings``, a ``pydantic-settings`` model that reads
    values from the INI file via ``IniFileSettingsSource``.  All application
    code should import the ``settings`` singleton and access fields directly:
    ``settings.user_id``, ``settings.files_folder_path``, etc.

**Dynamic settings** (read/written at runtime):
    Managed by ``config_manager`` (a ``DynamicConfigManager`` instance).
    Only components that need to *persist* user changes back to the INI file
    should import ``config_manager``.  Reading must still go through ``settings``;
    ``config_manager`` is write-only from the application's perspective.
"""

import configparser
from pathlib import Path
from typing import Any

from desktop.adapters.configManager import DynamicConfigManager
from pydantic import computed_field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# ---------------------------------------------------------------------------
# INI file location
# ---------------------------------------------------------------------------

CONFIG_FILE = Path(__file__).parent / "config.ini"

# ---------------------------------------------------------------------------
# INI settings source
# ---------------------------------------------------------------------------

# Mapping: Pydantic field name → (INI section, INI key)
_FIELD_MAP: dict[str, tuple[str, str]] = {
    "user_id": ("general", "userid"),
    "jog_step_x": ("interface.control.jog", "stepx"),
    "jog_step_y": ("interface.control.jog", "stepy"),
    "jog_step_z": ("interface.control.jog", "stepz"),
    "jog_feedrate": ("interface.control.jog", "feedrate"),
    "jog_units": ("interface.control.jog", "units"),
}


class IniFileSettingsSource(PydanticBaseSettingsSource):
    """Pydantic settings source that reads values from a .ini file.

    Values are parsed as raw strings and left to Pydantic for coercion into
    the declared field types, so no manual int/float conversion is needed here.
    """

    def __init__(self, settings_cls: type[BaseSettings], ini_file: Path) -> None:
        super().__init__(settings_cls)
        self._ini_file = ini_file

    # Required abstract method — individual field access is not used; we
    # return all values at once in __call__ instead.
    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:  # type: ignore[override]
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        parser = configparser.ConfigParser()
        parser.read(self._ini_file)

        result: dict[str, Any] = {}
        for field_name, (section, key) in _FIELD_MAP.items():
            if parser.has_option(section, key):
                result[field_name] = parser.get(section, key)
        return result


# ---------------------------------------------------------------------------
# Static settings (read once at startup)
# ---------------------------------------------------------------------------


class DesktopSettings(BaseSettings):
    """Validated application settings loaded from the INI config file.

    All fields are *read-only* after construction.  To persist a user change
    back to the INI file, use ``config_manager`` (see bottom of this module).
    """

    model_config = SettingsConfigDict(extra="ignore")

    # General
    user_id: int = 0

    # Jog defaults (section [interface.control.jog])
    jog_step_x: float = 0.25
    jog_step_y: float = 0.25
    jog_step_z: float = 0.25
    jog_feedrate: float = 200.0
    jog_units: int = 0

    # ---------------------------------------------------------------------------
    # Path fields — derived from the project structure, not configurable via INI.
    # ``parents[3]`` walks up: config.py → desktop/ → desktop/ → src/ → project root
    # ---------------------------------------------------------------------------

    @computed_field  # type: ignore[misc]
    @property
    def files_folder_path(self) -> Path:
        return Path(__file__).parents[3] / "gcode_files"

    @computed_field  # type: ignore[misc]
    @property
    def images_folder_path(self) -> Path:
        return Path(__file__).parents[3] / "thumbnails"

    @computed_field  # type: ignore[misc]
    @property
    def logs_folder_path(self) -> Path:
        return Path(__file__).parents[3] / "logs"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Only the INI file is used as a source; environment variables and
        # .env files are intentionally excluded from the desktop app.
        return (IniFileSettingsSource(settings_cls, CONFIG_FILE),)


# Singleton — the only instance application code should ever reference.
settings = DesktopSettings()

# ---------------------------------------------------------------------------
# Dynamic config manager (write path)
# ---------------------------------------------------------------------------

# Loaded once so it holds the current INI state in memory.  Components that
# persist runtime changes should use this object for *writes only*.
config_manager = DynamicConfigManager(CONFIG_FILE)
config_manager.load_config()
