"""File executor for the CNC Gateway.

Manages the lifecycle of executing a complete G-code file through the
`GrblController`.  Lines are fed into the controller's internal queue
at a controlled rate, respecting the GRBL buffer fill level.

File execution here is *non-blocking*: the main Gateway loop calls
`tick` periodically, which sends one line if conditions are met.
This allows the `CommandProcessor` to keep consuming priority commands
(pause/stop) between line sends.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import redis
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENT_FILE_PROGRESS,
    EVENT_FILE_STARTED,
    EVENTS_CHANNEL,
)

if TYPE_CHECKING:
    from core.utilities.grbl.grblController import GrblController

logger = logging.getLogger(__name__)

# Constants
SEND_INTERVAL = 0.10  # seconds between line sends
MAX_BUFFER_FILL = 75  # percentage — don't exceed this
PROGRESS_PUBLISH_INTERVAL = 1.0  # seconds between progress events


class FileExecutor:
    """Non-blocking G-code file executor for the Gateway."""

    def __init__(
        self,
        controller: GrblController,
        redis_conn: redis.Redis | None = None,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self.controller = controller
        self._redis = (
            redis_conn if redis_conn is not None else redis.Redis(host=host, port=port, db=db)
        )
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
            "processed_lines": self.controller.get_commands_count() if self._running else 0,
            "total_lines": self._total_lines,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, file_path: str, task_id: Optional[int] = None) -> None:
        """Open the G-code file and prepare for line-by-line execution."""
        if self._running:
            logger.warning("File execution already in progress, ignoring start request")
            return

        path = Path(file_path)
        if not path.is_file():
            logger.error("File not found: %s", file_path)
            self._publish_event(
                EVENT_FILE_FAILED,
                {
                    "task_id": task_id,
                    "error": f"File not found: {file_path}",
                },
            )
            return

        try:
            self._gcode = open(path, "r")
        except OSError as exc:
            logger.error("Cannot open file %s: %s", file_path, exc)
            self._publish_event(
                EVENT_FILE_FAILED,
                {
                    "task_id": task_id,
                    "error": str(exc),
                },
            )
            return

        # Count total lines
        self._total_lines = sum(1 for _ in self._gcode)
        self._gcode.seek(0)

        self._file_path = file_path
        self._task_id = task_id
        self._sent_lines = 0
        self._paused = False
        self._running = True
        self._last_send = 0.0
        self._last_progress_publish = 0.0

        self.controller.restart_commands_count()

        self._publish_event(
            EVENT_FILE_STARTED,
            {
                "task_id": task_id,
                "file_path": file_path,
                "total_lines": self._total_lines,
            },
        )
        logger.info("File execution started: %s (%d lines)", file_path, self._total_lines)

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
        logger.info("File execution stopped")

    def tick(self) -> None:
        """Called from the main loop.  Sends one line if conditions are met."""
        if not self._running or self._paused:
            return

        now = time.time()

        # Rate-limit sends
        if now - self._last_send < SEND_INTERVAL:
            return

        # Don't over-fill the GRBL buffer
        if self.controller.get_buffer_fill() > MAX_BUFFER_FILL:
            return

        # Check for CNC errors
        if self.controller.grbl_status.failed():
            error_msg = self.controller.grbl_status.get_error_message() or "Unknown error"
            self._close_file()
            self._publish_event(
                EVENT_FILE_FAILED,
                {
                    "task_id": self._task_id,
                    "error": error_msg,
                },
            )
            logger.error("File execution failed: %s", error_msg)
            self._reset_state()
            return

        # Check if GRBL finished processing (program end code detected)
        if self.controller.grbl_status.finished():
            self._close_file()
            self._publish_event(
                EVENT_FILE_FINISHED,
                {
                    "task_id": self._task_id,
                    "sent_lines": self._sent_lines,
                    "total_lines": self._total_lines,
                },
            )
            logger.info(
                "File execution finished: %d/%d lines",
                self._sent_lines,
                self._total_lines,
            )
            self._reset_state()
            return

        # Read and send next line
        if self._gcode is None:
            return
        line = self._gcode.readline()
        if not line:
            # EOF — wait for GRBL to finish processing remaining commands
            # The finished() flag will be set when the program end code is consumed
            # If no program end code, we still mark as finished after sending all lines
            self._close_file()
            self._publish_event(
                EVENT_FILE_FINISHED,
                {
                    "task_id": self._task_id,
                    "sent_lines": self._sent_lines,
                    "total_lines": self._total_lines,
                },
            )
            logger.info(
                "All lines sent: %d/%d",
                self._sent_lines,
                self._total_lines,
            )
            self._reset_state()
            return

        self.controller.send_command(line)
        self._sent_lines += 1
        self._last_send = now

        # Periodic progress event
        if now - self._last_progress_publish > PROGRESS_PUBLISH_INTERVAL:
            self._publish_event(EVENT_FILE_PROGRESS, self.get_progress())
            self._last_progress_publish = now

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self._running = False
        self._paused = False
        self._gcode = None
        self._file_path = ""
        self._task_id: Optional[int] = None
        self._sent_lines = 0
        self._total_lines = 0
        self._last_send = 0.0
        self._last_progress_publish = 0.0

    def _close_file(self) -> None:
        if self._gcode is not None:
            self._gcode.close()
            self._gcode = None

    def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        event = json.dumps({"type": event_type, **data})
        self._redis.publish(EVENTS_CHANNEL, event)
