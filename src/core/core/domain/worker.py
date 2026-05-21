"""Domain types for the worker subsystem.

These types describe the *shape* of data exchanged, independent of the underlying implementation.
"""

from typing import Optional

from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Broker inspection response types
# ---------------------------------------------------------------------------

# {"worker@host": {"ok": "pong"}}
PingResponse = dict[str, dict[str, str]]

# {"worker@host": ["task_name", ...]}
ActiveTasksResponse = dict[str, list[str]]

# {"worker@host": ["task_name", ...]}
RegisteredTasksResponse = dict[str, list[str]]


class WorkerNodeStats(TypedDict, total=False):
    """Stats for a single worker node."""

    pid: int
    uptime: int
    clock: str
    total: dict
    prefetch_count: int
    pool: dict
    broker: dict
    rusage: object


# {"worker@host": WorkerNodeStats}
StatsResponse = dict[str, WorkerNodeStats]

# ---------------------------------------------------------------------------
# WorkerStatus — full snapshot returned by worker
# ---------------------------------------------------------------------------

WorkerStatus = TypedDict(
    "WorkerStatus",
    {
        "connected": bool,
        "running": bool,
        "stats": Optional[StatsResponse],
        "registered_tasks": Optional[RegisteredTasksResponse],
        "active_tasks": Optional[ActiveTasksResponse],
    },
)
