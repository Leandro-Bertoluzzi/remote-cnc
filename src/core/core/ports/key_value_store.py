"""Key-value store port — the minimal interface for storing and retrieving values by key."""

from __future__ import annotations

from typing import Any, Protocol, Union, runtime_checkable


@runtime_checkable
class IKeyValueStore(Protocol):
    """Structural interface for a synchronous key-value store."""

    def get(self, name: str) -> bytes | None:
        """Return the value at *name*, or ``None`` if the key does not exist."""
        ...

    def set(
        self,
        name: str,
        value: Union[bytes, str, int, float],
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
        **kwargs: Any,
    ) -> bool | None:
        """Set the value at *name*."""
        ...

    def exists(self, *names: str) -> int:
        """Return the number of *names* that exist."""
        ...

    def delete(self, *names: str) -> int:
        """Delete one or more keys. Returns the count of keys removed."""
        ...

    def expire(self, name: str, time: int) -> bool:
        """Set an expiry of *time* seconds on *name*. Returns ``True`` if set."""
        ...

    def llen(self, name: str) -> int:
        """Return the length of the list at *name*."""
        ...

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: Union[bytes, str, int, float],
    ) -> Any:
        """Evaluate a Lua *script* server-side with *numkeys* key arguments."""
        ...
