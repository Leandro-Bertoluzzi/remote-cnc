"""File executor for the CNC Gateway.

Manages the lifecycle of executing a complete G-code file through the
CNC controller.  Lines are fed into the controller's internal queue
at a controlled rate, respecting the command buffer fill level.

File execution here is *non-blocking*: the main Gateway loop calls
`tick` periodically, which sends one line if conditions are met.
This allows the `CommandProcessor` to keep consuming priority commands
(pause/stop) between line sends.
"""

from __future__ import annotations

import json
import re
import time
from collections import deque
from typing import Any, Callable, Optional

from core.domain.gateway import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENT_FILE_STARTED,
    EVENTS_CHANNEL,
)
from core.ports.file_storage import IFileStorage
from core.ports.logger import ILogger
from core.ports.pubsub_client import IPubSubClient

from gateway.ports.cnc_controller import CncController

GCODE_PROGRAM_END_CODES = ["M2", "M02", "M30"]

# Constants
SEND_INTERVAL = 0.10  # seconds between line sends
MAX_BUFFER_FILL = 75  # percentage — don't exceed this
PROGRESS_PUBLISH_INTERVAL = 1.0  # seconds between progress events
STALL_TIMEOUT = 60.0  # seconds without an 'ok' (with pending commands) before declaring stall


class FileExecutor:
    """Non-blocking G-code file executor for the Gateway."""

    def __init__(
        self,
        controller: CncController,
        pubsub_client: IPubSubClient,
        storage: IFileStorage,
        logger_factory: Callable[[str | None], tuple[ILogger, Callable[[], None]]],
    ):
        self.controller = controller
        self._pubsub_client = pubsub_client
        self._storage = storage
        self._logger_factory = logger_factory

        # The logger is initialized with a clean state
        self._logger, self._logger_cleanup = self._logger_factory(None)

        # Reset all execution state to defaults
        self._reset_state()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    def get_progress(self) -> dict[str, Any]:
        return {
            "task_id": self._task_id,
            "file_path": self._file_path,
            "sent_lines": self._sent_lines,
            "processed_lines": self._processed_lines if self._running else 0,
            "total_lines": self._total_lines,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(
        self,
        file_path: str,
        task_id: Optional[int] = None,
        shared_logger_name: Optional[str] = None,
    ) -> None:
        """Open the G-code file and prepare for line-by-line execution.

        If *shared_logger_name* is given, execution logs are appended to the shared logs file.
        """
        if self._running:
            self._logger.warning("File execution already in progress, ignoring start request")
            return

        # Support logging to a shared file if a logger name is given
        self._logger, self._logger_cleanup = self._logger_factory(shared_logger_name)

        try:
            self._gcode = self._storage.open_for_reading(file_path)
        except Exception as exc:
            self._logger.error("Cannot open file %s: %s", file_path, exc)
            self._publish_event(
                EVENT_FILE_FAILED,
                {
                    "task_id": task_id,
                    "error": str(exc),
                },
            )
            self._reset_state()
            return

        # Count total lines
        self._total_lines = sum(1 for _ in self._gcode)
        self._gcode.seek(0)

        self._file_path = file_path
        self._task_id = task_id
        self._sent_lines = 0
        self._processed_lines = 0
        self._pending_file_cmds: deque[str] = deque()
        self._paused = False
        self._running = True
        self._draining = False
        self._last_send = 0.0
        self._last_ok_time = time.time()

        self.controller.register_ok_hook(self._on_ok)

        self._publish_event(
            EVENT_FILE_STARTED,
            {
                "task_id": task_id,
                "file_path": file_path,
                "total_lines": self._total_lines,
            },
        )
        self._logger.info("File execution started: %s (%d lines)", file_path, self._total_lines)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def stop(self) -> None:
        """Stop file execution (user-requested or error)."""
        if not self._running:
            return
        self._close_file()
        self._publish_event(
            EVENT_FILE_FAILED,
            {
                "task_id": self._task_id,
                "error": "Stopped by user",
            },
        )
        self._reset_state()
        self._logger.info("File execution stopped")

    def tick(self) -> None:
        """Called from the main loop. Sends one line if conditions are met."""
        if not self._running:
            return

        now = time.time()

        # Check for CNC errors — applies in all active states, including draining
        if self.controller.failed():
            error_msg = self.controller.get_error_message() or "Unknown error"
            self._close_file()
            self._publish_event(
                EVENT_FILE_FAILED,
                {
                    "task_id": self._task_id,
                    "error": error_msg,
                },
            )
            self._logger.error("File execution failed: %s", error_msg)
            self._reset_state()
            return

        # Stall watchdog — also fires during draining: all pending acks must eventually arrive
        pending = len(self._pending_file_cmds)
        if pending > 0 and (now - self._last_ok_time) > STALL_TIMEOUT:
            self._on_stall()
            return

        # Draining mode: all lines have been sent; wait until every pending ok arrives
        if self._draining:
            self._try_finish_drain()
            return

        if self._paused:
            return

        # Rate-limit sends
        if now - self._last_send < SEND_INTERVAL:
            return

        # Don't over-fill the command buffer
        if self.controller.get_buffer_fill() > MAX_BUFFER_FILL:
            return

        # Read and send next line
        if self._gcode is None:
            return

        line = self._gcode.readline()
        if not line:
            # EOF — all lines sent; enter draining mode to wait for pending acks
            self._close_file()
            self._draining = True
            self._try_finish_drain()
            return

        stripped = line.strip()
        is_empty = not stripped
        is_comment = bool(re.match(r"(^\(.*\)$)|(^;.*)", stripped))

        # Lines discarded without sending an actual command still count as processed
        if is_empty or is_comment:
            self._processed_lines += 1
            self._sent_lines += 1
            self._last_send = now
        else:
            # Detect program-end G-code before enqueueing
            is_program_end = stripped.upper() in GCODE_PROGRAM_END_CODES

            self._pending_file_cmds.append(stripped)
            self.controller.send_command(line)
            self._sent_lines += 1
            self._last_send = now

            if is_program_end:
                # Enter draining mode; the FINISHED event is deferred until the
                # M2/M30 ok is received and _pending_file_cmds becomes empty.
                self._close_file()
                self._draining = True
                return

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _try_finish_drain(self) -> None:
        """If no pending acks remain, publish the finished event and reset state."""
        if self._pending_file_cmds:
            return

        self._publish_event(
            EVENT_FILE_FINISHED,
            {
                "task_id": self._task_id,
                "sent_lines": self._sent_lines,
                "processed_lines": self._processed_lines,
                "total_lines": self._total_lines,
            },
        )
        self._logger.info(
            "File execution finished: %d lines processed",
            self._total_lines,
        )
        self._reset_state()

    def _on_ok(self, done_cmd: str) -> None:
        """Called by the controller for every ``ok`` response while a file is running.

        Only updates ``_processed_lines`` when the ``ok`` corresponds to the head
        of the file-command queue.  Out-of-band oks (e.g. parser state queries, jog commands) are
        silently ignored.
        """
        if self._running and self._pending_file_cmds and done_cmd == self._pending_file_cmds[0]:
            self._pending_file_cmds.popleft()
            self._processed_lines += 1
            self._last_ok_time = time.time()

    def _on_stall(self) -> None:
        """Called when the watchdog detects a stall.

        Fails the current file execution without touching the serial thread.
        """
        if not self._running:
            return

        self._close_file()
        self._publish_event(
            EVENT_FILE_FAILED,
            {
                "task_id": self._task_id,
                "error": "Device stall detected",
            },
        )
        self._logger.error("File execution failed: device stall detected")
        self._reset_state()

    def _reset_state(self) -> None:
        self.controller.register_ok_hook(None)
        self._running = False
        self._draining = False
        self._paused = False
        self._gcode = None
        self._file_path = ""
        self._task_id: Optional[int] = None
        self._sent_lines = 0
        self._processed_lines = 0
        self._pending_file_cmds: deque[str] = deque()
        self._total_lines = 0
        self._last_send = 0.0
        self._last_ok_time = 0.0

        # Reset logger to a clean state
        self._logger_cleanup()
        self._logger, self._logger_cleanup = self._logger_factory(None)

    def _close_file(self) -> None:
        if self._gcode is not None:
            self._gcode.close()
            self._gcode = None

    def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        event = json.dumps({"type": event_type, **data})
        self._pubsub_client.publish(EVENTS_CHANNEL, event)
