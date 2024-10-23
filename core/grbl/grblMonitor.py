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

_LOG_LEVELS = ['critical', 'error', 'warning', 'info', 'debug']


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

    def _log(self, level: str, log: str, queue: bool = False, exc_info: bool = None):
        if level not in _LOG_LEVELS:
            return

        log_method = getattr(self.logger, level)
        if exc_info is not None:
            log_method(log, exc_info=exc_info)
        else:
            log_method(log)

        if queue:
            self.queueLog(log)

    def debug(self, log: str, queue: bool = False):
        self._log('debug', log, queue=queue)

    def info(self, log: str, queue: bool = False):
        self._log('info', log, queue=queue)

    def warning(self, log: str, queue: bool = False):
        self._log('warning', log, queue=queue)

    def error(self, log: str, queue: bool = False):
        self._log('error', log, queue=queue)

    def critical(self, log: str, exc_info: bool = True, queue: bool = False):
        self._log('critical', log, queue=queue, exc_info=exc_info)

    def sent(self, command: str, debug: bool = False):
        command = command.strip()   # Strip all EOL characters for consistency
        if debug:
            self.logger.debug('[Sent] command: {}'.format(command))
            return
        self.logger.info('[Sent] command: {}'.format(command))
        self.queueLog(command)

        # Publish in PubSub
        self._publish('sent', command)

    def received(self, message: str, msgType: Optional[str], payload: dict[str, str]):
        received_str = '[Received] Message from GRBL: {}'.format(message)
        parsed_str = '[Parsed] Message type: {}| Payload: {}'.format(msgType, payload)

        if (msgType == GRBL_MSG_STATUS):
            self.logger.debug(received_str)
            self.logger.debug(parsed_str)
            return

        self.logger.info(received_str)
        self.logger.info(parsed_str)
        self.queueLog(message)

        # Publish in PubSub
        self._publish('received', message)

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

    # PUBSUB

    def _publish(self, msgType: str, message: str):
        pubsub_message = json.dumps({
            'type': msgType,
            'message': message
        })
        self.redis.publish(PUBSUB_CHANNEL, pubsub_message)
