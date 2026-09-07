"""Port to read configuration values."""

from pathlib import Path
from typing import Protocol


class ISettingsReader(Protocol):
    """Read-only view of the desktop application settings."""

    @property
    def user_id(self) -> int: ...

    @property
    def jog_step_x(self) -> float: ...

    @property
    def jog_step_y(self) -> float: ...

    @property
    def jog_step_z(self) -> float: ...

    @property
    def jog_feedrate(self) -> float: ...

    @property
    def jog_units(self) -> int: ...

    @property
    def files_folder_path(self) -> Path: ...

    @property
    def images_folder_path(self) -> Path: ...

    @property
    def logs_folder_path(self) -> Path: ...
