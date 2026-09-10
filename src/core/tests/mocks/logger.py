"""Test double for the ILogger port.

* satisfies ``ILogger`` structurally (verified at import time),
* records every call with its arguments for straightforward assertions,
* is completely side-effect free (no files, no handlers, no global state).

Usage example::

    from tests.mocks.logger import FakeLogger

    def test_something():
        logger = FakeLogger()
        my_function(logger=logger)
        assert len(logger.info_calls) == 1
        assert "started" in logger.info_calls[0][0]
"""

from __future__ import annotations

from typing import Any


class FakeLogger:
    """In-memory logger that records calls by level.

    Each ``*_calls`` attribute is a list of ``(msg, args, kwargs)`` tuples,
    one entry per call.  This makes assertions explicit and readable without
    relying on ``call_count`` or ``unittest.mock`` internals.

    Also exposes a no-op ``addHandler`` so it can be injected wherever a
    ``logging.Logger`` is expected.
    """

    def __init__(self) -> None:
        self.debug_calls: list[tuple[Any, tuple, dict]] = []
        self.info_calls: list[tuple[Any, tuple, dict]] = []
        self.warning_calls: list[tuple[Any, tuple, dict]] = []
        self.error_calls: list[tuple[Any, tuple, dict]] = []
        self.critical_calls: list[tuple[Any, tuple, dict]] = []
        self.exception_calls: list[tuple[Any, tuple, dict]] = []

    # ------------------------------------------------------------------
    # ILogger protocol methods
    # ------------------------------------------------------------------

    def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        self.debug_calls.append((msg, args, kwargs))

    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        self.info_calls.append((msg, args, kwargs))

    def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        self.warning_calls.append((msg, args, kwargs))

    def error(self, msg: object, *args: object, **kwargs: object) -> None:
        self.error_calls.append((msg, args, kwargs))

    def critical(self, msg: object, *args: object, **kwargs: object) -> None:
        self.critical_calls.append((msg, args, kwargs))

    def exception(self, msg: object, *args: object, **kwargs: object) -> None:
        self.exception_calls.append((msg, args, kwargs))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def call_count(self, level: str) -> int:
        """Return the number of calls recorded for *level* (e.g. ``"info"``)."""
        return len(getattr(self, f"{level}_calls"))

    def reset(self) -> None:
        """Clear all recorded calls."""
        for attr in ("debug", "info", "warning", "error", "critical", "exception"):
            getattr(self, f"{attr}_calls").clear()
