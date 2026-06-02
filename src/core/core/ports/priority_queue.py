"""Priority queue port — the minimal interface for a priority queue."""

from __future__ import annotations

from typing import Protocol, Sequence, Union, runtime_checkable


@runtime_checkable
class IPriorityQueue(Protocol):
    """Structural interface for a synchronous priority queue."""

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

    def llen(self, name: str) -> int:
        """Return the length of the list at *name*."""
        ...
