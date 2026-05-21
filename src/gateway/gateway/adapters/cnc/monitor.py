import json
import logging
from queue import Empty, Queue
from typing import Optional

from core.ports.redis_client import RedisClient

from gateway.adapters.cnc.parsers.grblMsgTypes import GRBL_MSG_STATUS

# Constants
PUBSUB_CHANNEL = "grbl_messages"
LOG_LEVELS = ["critical", "error", "warning", "info", "debug"]


class GrblMonitor:
    def __init__(self, logger: logging.Logger, redis_conn: RedisClient):
        # Configure logs queue for external monitor
        self.logs_queue: Queue[str] = Queue()

        # Configure logger
        self.logger = logger

        # Redis connection for publishing updates to external apps
        self.redis = redis_conn

    def __del__(self):
        # Removes the file handler from the logger
        for h in self.logger.handlers:
            if isinstance(h, logging.FileHandler):
                self.logger.removeHandler(h)

    # LOGGER

    def debug(self, log: str, queue: bool = False):
        self.logger.debug(log)
        if queue:
            self.queue_log(log)

    def info(self, log: str, queue: bool = False):
        self.logger.info(log)
        if queue:
            self.queue_log(log)

    def warning(self, log: str, queue: bool = False):
        self.logger.warning(log)
        if queue:
            self.queue_log(log)

    def error(self, log: str, queue: bool = False):
        self.logger.error(log)
        if queue:
            self.queue_log(log)

    def critical(self, log: str, exc_info: bool = True, queue: bool = False):
        self.logger.critical(log, exc_info=exc_info)
        if queue:
            self.queue_log(log)

    def sent(self, command: str, debug: bool = False):
        command = command.strip()  # Strip all EOL characters for consistency
        if debug:
            self.logger.debug("[Sent] command: {}".format(command))
            return
        self.logger.info("[Sent] command: {}".format(command))
        self.queue_log(command)

        # Publish in PubSub
        self._publish("sent", command)

    def received(self, message: str, msgType: Optional[str], payload: dict[str, str]):
        received_str = "[Received] Message from GRBL: {}".format(message)
        parsed_str = "[Parsed] Message type: {}| Payload: {}".format(msgType, payload)

        if msgType == GRBL_MSG_STATUS:
            self.logger.debug(received_str)
            self.logger.debug(parsed_str)
            return

        self.logger.info(received_str)
        self.logger.info(parsed_str)
        self.queue_log(message)

        # Publish in PubSub
        self._publish("received", message)

    # LOGS QUEUE MANAGEMENT

    def queue_log(self, log: str):
        """
        Adds a message to the log queue.
        This queue can be accessed by an external monitor.
        """
        self.logs_queue.put(log)

    def has_logs(self) -> bool:
        """Tell if there are any queued logs."""
        return self.logs_queue.qsize() > 0

    def get_log(self) -> str:
        """Returns a log from the log queue."""
        try:
            return self.logs_queue.get_nowait()
        except Empty:
            return ""

    # PUBSUB

    def _publish(self, msgType: str, message: str):
        pubsub_message = json.dumps({"type": msgType, "message": message})
        self.redis.publish(PUBSUB_CHANNEL, pubsub_message)
