"""Command processor for the CNC Gateway.

Consumes commands from the priority Redis queues via ``BLPOP`` and
dispatches them to the appropriate handler on the GrblController.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import redis
from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT
from core.utilities.gateway.constants import (
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_SOFT_RESET,
    ACTION_STOP,
    ALL_QUEUES,
    MSG_COMMAND,
    MSG_DISCONNECT,
    MSG_FILE_START,
    MSG_FILE_STOP,
    MSG_JOG,
    MSG_QUERY,
    MSG_REALTIME,
)
from core.utilities.grbl.grblUtils import build_jog_command

if TYPE_CHECKING:
    from core.utilities.grbl.grblController import GrblController

    from gateway.fileExecutor import FileExecutor
    from gateway.sessionManager import SessionManager

logger = logging.getLogger(__name__)

# BLPOP timeout in seconds — controls how often the loop can check for
# shutdown signals when no commands are queued.
BLPOP_TIMEOUT = 1


class CommandProcessor:
    """Reads from the priority queues and dispatches commands.

    The processor runs in the main thread of the Gateway. It blocks on
    ``BLPOP`` for up to *BLPOP_TIMEOUT* seconds, then returns to let the
    caller perform housekeeping (status publishing, etc.).
    """

    def __init__(
        self,
        controller: GrblController,
        session_manager: SessionManager,
        file_executor: FileExecutor,
        redis_conn: redis.Redis | None = None,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB_STORAGE,
    ):
        self.controller = controller
        self.session_manager = session_manager
        self.file_executor = file_executor
        self._redis = (
            redis_conn if redis_conn is not None else redis.Redis(host=host, port=port, db=db)
        )
        self._disconnect_requested = False

    @property
    def should_stop(self) -> bool:
        return self._disconnect_requested

    # ------------------------------------------------------------------
    # Main loop entry point
    # ------------------------------------------------------------------

    def process_one(self) -> bool:
        """Block until a command is available, then process it.

        Returns ``True`` if a command was processed, ``False`` if the
        timeout elapsed with no command.
        """
        result = self._redis.blpop(ALL_QUEUES, timeout=BLPOP_TIMEOUT)
        if result is None:
            return False

        queue_name_bytes, raw_message = result
        queue_name = (
            queue_name_bytes.decode()
            if isinstance(queue_name_bytes, bytes)
            else str(queue_name_bytes)
        )

        try:
            message = json.loads(raw_message)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Malformed message on %s: %s", queue_name, raw_message)
            return True

        self._dispatch(message, queue_name)
        return True

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, message: dict[str, Any], queue_name: str) -> None:
        msg_type = message.get("type", "")
        session_id = message.get("session_id", "")
        payload = message.get("payload", {})

        # Validate session (queries are exempt)
        if msg_type != MSG_QUERY and not self.session_manager.validate_session(session_id):
            logger.warning(
                "Rejected %s from invalid session %s",
                msg_type,
                session_id[:8] if session_id else "(empty)",
            )
            return

        if msg_type == MSG_REALTIME:
            self._handle_realtime(payload)
        elif msg_type == MSG_COMMAND:
            self._handle_command(payload)
        elif msg_type == MSG_JOG:
            self._handle_jog(payload)
        elif msg_type == MSG_FILE_START:
            self._handle_file_start(payload)
        elif msg_type == MSG_FILE_STOP:
            self._handle_file_stop()
        elif msg_type == MSG_QUERY:
            self._handle_query(payload)
        elif msg_type == MSG_DISCONNECT:
            self._handle_disconnect(session_id)
        else:
            logger.warning("Unknown message type: %s", msg_type)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_realtime(self, payload: dict[str, Any]) -> None:
        action = payload.get("action", "")
        if action == ACTION_PAUSE:
            self.controller.set_paused(True)
            if self.file_executor.is_running:
                self.file_executor.pause()
            logger.info("Pause requested")
        elif action == ACTION_RESUME:
            self.controller.set_paused(False)
            if self.file_executor.is_running:
                self.file_executor.resume()
            logger.info("Resume requested")
        elif action == ACTION_STOP:
            self.controller.grbl_soft_reset()
            if self.file_executor.is_running:
                self.file_executor.stop()
            logger.info("Stop requested")
        elif action == ACTION_SOFT_RESET:
            self.controller.grbl_soft_reset()
            logger.info("Soft reset requested")
        else:
            logger.warning("Unknown realtime action: %s", action)

    def _handle_command(self, payload: dict[str, Any]) -> None:
        command = payload.get("command", "")
        if command:
            self.controller.send_command(command)
            logger.debug("Command queued: %s", command.strip())

    def _handle_jog(self, payload: dict[str, Any]) -> None:
        jog_cmd = build_jog_command(
            payload.get("x", 0),
            payload.get("y", 0),
            payload.get("z", 0),
            payload.get("feedrate", 0),
            units=payload.get("units"),
            distance_mode=payload.get("distance_mode"),
            machine_coordinates=payload.get("machine_coordinates", False),
        )
        self.controller.send_command(jog_cmd)
        logger.debug("Jog command queued: %s", jog_cmd)

    def _handle_file_start(self, payload: dict[str, Any]) -> None:
        file_path = payload.get("file_path", "")
        task_id = payload.get("task_id")
        if not file_path:
            logger.error("file_start without file_path")
            return
        self.file_executor.start(file_path, task_id)
        logger.info("File execution started: %s (task %s)", file_path, task_id)

    def _handle_file_stop(self) -> None:
        if self.file_executor.is_running:
            self.file_executor.stop()
            logger.info("File execution stopped by user")

    def _handle_query(self, payload: dict[str, Any]) -> None:
        query_type = payload.get("query", "")
        queries = {
            "status": self.controller.queryStatusReport,
            "parserstate": self.controller.query_gcode_parser_state,
            "settings": self.controller.query_grbl_settings,
            "params": self.controller.query_grbl_params,
            "build_info": self.controller.query_build_info,
            "help": self.controller.query_grbl_help,
        }
        handler = queries.get(query_type)
        if handler:
            handler()
            logger.debug("Query executed: %s", query_type)
        else:
            logger.warning("Unknown query type: %s", query_type)

    def _handle_disconnect(self, session_id: str) -> None:
        logger.info("Disconnect requested by session %s", session_id[:8])
        self._disconnect_requested = True
