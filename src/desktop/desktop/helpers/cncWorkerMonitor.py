"""Monitor CNC task execution via Gateway Redis PubSub.

Subscribes to the ``grbl_status`` and ``cnc:events`` channels published
by the CNC Gateway.  Emits Qt signals that the UI can connect to for
real-time progress and lifecycle updates.
"""

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

from desktop.services.deviceService import DeviceService

logger = logging.getLogger(__name__)


class CncWorkerMonitor(QObject):
    """Monitors CNC task execution through the Gateway's PubSub channels.

    * ``grbl_status``  — periodic status + file progress (every ~100 ms)
    * ``cnc:events``   — discrete lifecycle events (finished / failed)

    Signals are thread-safe (``Qt.AutoConnection`` queues cross-thread
    emissions to the main event loop).
    """

    # SIGNALS
    task_new_status = pyqtSignal(int, int, int, object, object)
    task_finished = pyqtSignal()
    task_failed = pyqtSignal(str)

    # CONSTRUCTOR

    def __init__(self):
        super().__init__()
        self._gateway = GatewayClient()
        self._thread: threading.Thread | None = None
        self._running = False

    # FLOW CONTROL

    def start_task_monitor(self):
        """Start listening for Gateway events in a background thread."""
        if self._running:
            logger.warning("Task monitor already running, ignoring duplicate start")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop_task_monitor(self):
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
            logger.exception("Error in CncWorkerMonitor listener thread")
        finally:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except Exception:
                pass

    def _handle_status(self, data: dict) -> None:
        """Process a ``grbl_status`` message — relay file progress."""
        file_progress = data.get("file_progress")
        if file_progress is None:
            return

        self.task_new_status.emit(
            file_progress.get("sent_lines", 0),
            file_progress.get("processed_lines", 0),
            file_progress.get("total_lines", 0),
            data.get("status"),
            data.get("parserstate"),
        )

    def _handle_event(self, event: dict) -> None:
        """Process a ``cnc:events`` message — detect finished/failed."""
        event_type = event.get("type", "")

        if event_type == EVENT_FILE_FINISHED:
            self._running = False
            try:
                DeviceService.set_device_enabled(False)
            except Exception:
                logger.warning("Could not disable device after task success")
            self.task_finished.emit()

        elif event_type == EVENT_FILE_FAILED:
            self._running = False
            try:
                DeviceService.set_device_enabled(False)
            except Exception:
                logger.warning("Could not disable device after task failure")
            self.task_failed.emit(event.get("error", "Error desconocido"))
