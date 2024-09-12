import json
import logging
from .parsers.grblMsgTypes import GRBL_MSG_STATUS
from queue import Empty, Queue
from typing import Optional

try:
    from ..utils.redisPubSubManager import RedisPubSubManagerSync
except ImportError:
    from utils.redisPubSubManager import RedisPubSubManagerSync

# Constants
PUBSUB_CHANNEL = 'grbl_messages'


class GrblMonitor:
    def __init__(self, logger: logging.Logger):
        # Configure logs queue for external monitor
        self.queue_log: Queue[str] = Queue()

        # Configure logger
        self.logger = logger

        # Start a PubSub manager to notify updates to external apps
        self.redis = RedisPubSubManagerSync()
        self.redis.connect()

    def __del__(self):
        # Removes the file handler from the logger
        for h in self.logger.handlers:
            if isinstance(h, logging.FileHandler):
                self.logger.removeHandler(h)
        # Unsubscribes from PubSub
        self.redis.disconnect()

    # LOGGER

    def debug(self, log: str, queue: bool = False):
        self.logger.debug(log)
        if queue:
            self.queueLog(log)

    def info(self, log: str, queue: bool = False):
        self.logger.info(log)
        if queue:
            self.queueLog(log)

    def warning(self, log: str, queue: bool = False):
        self.logger.warning(log)
        if queue:
            self.queueLog(log)

    def error(self, log: str, queue: bool = False):
        self.logger.error(log)
        if queue:
            self.queueLog(log)

    def critical(self, log: str, exc_info: bool = True, queue: bool = False):
        self.logger.critical(log, exc_info=exc_info)
        if queue:
            self.queueLog(log)

    def sent(self, command: str, debug: bool = False):
        command = command.strip()   # Strip all EOL characters for consistency
        if debug:
            self.logger.debug('[Sent] command: %s', command)
            return
        self.logger.info('[Sent] command: %s', command)
        self.queueLog(command)
        # Publish in PubSub
        pubsub_message = json.dumps({
            'type': 'sent',
            'message': command
        })
        self.redis.publish(PUBSUB_CHANNEL, pubsub_message)

    def received(self, message: str, msgType: Optional[str], payload: dict[str, str]):
        if (msgType == GRBL_MSG_STATUS):
            self.logger.debug('[Received] Message from GRBL: %s', message)
            self.logger.debug('[Parsed] Message type: %s| Payload: %s', msgType, payload)
            return

        self.logger.info('[Received] Message from GRBL: %s', message)
        self.logger.info('[Parsed] Message type: %s| Payload: %s', msgType, payload)
        self.queueLog(message)
        # Publish in PubSub
        pubsub_message = json.dumps({
            'type': 'received',
            'message': message
        })
        self.redis.publish(PUBSUB_CHANNEL, pubsub_message)

    # LOGS QUEUE MANAGEMENT

    def queueLog(self, log: str):
        """Adds a message to the log queue.
        This queue can be accessed by an external monitor.
        """
        self.queue_log.put(log)

    def hasLogs(self) -> bool:
        """Tell if there are any queued logs.
        """
        return self.queue_log.qsize() > 0

    def getLog(self) -> str:
        """Returns a log from the log queue.
        """
        try:
            return self.queue_log.get_nowait()
        except Empty:
            return ''
