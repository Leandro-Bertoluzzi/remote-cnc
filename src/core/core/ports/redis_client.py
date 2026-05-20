"""RedisClient port — the minimal Redis interface used across all modules.

Any object that implements these methods is a valid ``RedisClient``.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, Union, runtime_checkable


@runtime_checkable
class RedisClient(Protocol):
    """Structural interface for a synchronous Redis connection."""

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

    def publish(self, channel: str, message: Union[bytes, str, memoryview]) -> int:
        """Publish *message* to *channel*. Returns the number of subscribers."""
        ...

    def blpop(
        self,
        keys: Union[str, Sequence[str]],
        timeout: float = 0,
    ) -> tuple[bytes, bytes] | None:
        """Remove and return the first element from a list, blocking until
        one is available or *timeout* elapses.  Returns ``None`` on timeout.
        """
        ...

    def rpush(self, name: str, *values: Union[bytes, str, int, float]) -> int:
        """Append one or more *values* to the tail of the list at *name*.
        Returns the new length of the list.
        """
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
