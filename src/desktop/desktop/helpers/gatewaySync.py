"""Real-time CNC status synchronisation via Gateway PubSub.

``GatewaySync`` subscribes to the ``grbl_status`` and ``cnc:events``
Redis PubSub channels published by the CNC Gateway and emits
Qt signals consumed by the :class:`ControlView`.

Signal interface
----------------
* ``new_status(status, parserstate)`` — periodic controller state
* ``file_progress(sent, processed, total)`` — file-execution progress
* ``file_finished()`` — G-code file completed successfully
* ``file_failed(error_msg)`` — G-code file execution failed

See DR-0001 for the architecture rationale.
"""

from __future__ import annotations

import json
import logging
import threading

from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENTS_CHANNEL,
    STATUS_CHANNEL,
)
from core.utilities.gateway.gatewayClient import GatewayClient
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class GatewaySync(QObject):
    """Subscribe to Gateway PubSub channels and emit Qt signals."""

    # SIGNALS
    new_status = pyqtSignal(object, object)
    file_progress = pyqtSignal(int, int, int)
    file_finished = pyqtSignal()
    file_failed = pyqtSignal(str)

    # CONSTRUCTOR

    def __init__(self) -> None:
        super().__init__()
        self._gateway = GatewayClient()
        self._thread: threading.Thread | None = None
        self._running = False

    # FLOW CONTROL

    def start_monitor(self) -> None:
        """Start listening for Gateway status updates in a background thread."""
        if self._running:
            logger.warning("GatewaySync already running, ignoring duplicate start")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop_monitor(self) -> None:
        """Signal the listener thread to stop."""
        self._running = False

    # INTERNAL

    def _listen(self) -> None:
        """Background thread: subscribe to PubSub and dispatch messages."""
        pubsub = self._gateway.subscribe_channels(STATUS_CHANNEL, EVENTS_CHANNEL)
        try:
            while self._running:
                raw = pubsub.get_message(timeout=1.0)
                if raw is None or raw["type"] != "message":
                    continue

                channel = raw["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()

                try:
                    data = json.loads(raw["data"])
                except (json.JSONDecodeError, TypeError):
                    continue

                if channel == STATUS_CHANNEL:
                    self._handle_status(data)
                elif channel == EVENTS_CHANNEL:
                    self._handle_event(data)
        except Exception:
            logger.exception("Error in GatewaySync listener thread")
        finally:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass

    def _handle_status(self, data: dict) -> None:
        """Process a ``grbl_status`` message."""
        status = data.get("status")
        parserstate = data.get("parserstate")
        if status and parserstate:
            self.new_status.emit(status, parserstate)

        file_prog = data.get("file_progress")
        if file_prog:
            self.file_progress.emit(
                file_prog.get("sent_lines", 0),
                file_prog.get("processed_lines", 0),
                file_prog.get("total_lines", 0),
            )

    def _handle_event(self, data: dict) -> None:
        """Process a ``cnc:events`` message."""
        event_type = data.get("type")
        if event_type == EVENT_FILE_FINISHED:
            self.file_finished.emit()
        elif event_type == EVENT_FILE_FAILED:
            self.file_failed.emit(data.get("error", "Error desconocido"))
