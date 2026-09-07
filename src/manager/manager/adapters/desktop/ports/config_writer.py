"""Port to write dynamic configuration values."""

from typing import Protocol


class IConfigWriter(Protocol):
    """Write-only interface for persisting mutable runtime settings."""

    def set_str(self, section: str, name: str, value: str) -> None: ...

    def set_int(self, section: str, name: str, value: int) -> None: ...

    def set_float(self, section: str, name: str, value: float) -> None: ...

    def set_bool(self, section: str, name: str, value: bool) -> None: ...

    def save_config(self) -> None: ...
