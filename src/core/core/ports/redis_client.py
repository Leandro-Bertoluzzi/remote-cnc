"""RedisClient port — the minimal Redis interface."""

from __future__ import annotations

from typing import Any, Iterator, Optional, Protocol, Sequence, Union, runtime_checkable

from typing_extensions import TypedDict


class PubSubMessage(TypedDict):
    """Shape of a message dict returned by IPubSub.get_message() / IPubSub.listen()."""

    type: str
    channel: Union[str, bytes]
    data: Union[bytes, str, int]


@runtime_checkable
class IPubSub(Protocol):
    """Minimal PubSub interface used across the codebase."""

    def subscribe(self, *channels: str, **kwargs: Any) -> None:
        """Subscribe to one or more channels."""
        ...

    def unsubscribe(self, *channels: str) -> None:
        """Unsubscribe from channels (or all if none given)."""
        ...

    def get_message(
        self,
        ignore_subscribe_messages: bool = False,
        timeout: float = 0.0,
    ) -> Optional[PubSubMessage]:
        """Return the next available message, or ``None`` if none ready."""
        ...

    def listen(self) -> Iterator[PubSubMessage]:
        """Block and yield messages as they arrive."""
        ...

    def close(self) -> None:
        """Release the underlying connection."""
        ...


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

    def pubsub(self, **kwargs: Any) -> IPubSub:
        """Return a PubSub handle for channel subscriptions."""
        ...
