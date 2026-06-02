"""PubSubClient port — the minimal PubSub interface."""

from __future__ import annotations

from typing import Any, Iterator, Optional, Protocol, Union, runtime_checkable

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
class IPubSubClient(Protocol):
    """Structural interface for a synchronous PubSub client."""

    def publish(self, channel: str, message: Union[bytes, str, memoryview]) -> int:
        """Publish *message* to *channel*. Returns the number of subscribers."""
        ...

    def pubsub(self, **kwargs: Any) -> IPubSub:
        """Return a PubSub handle for channel subscriptions."""
        ...
