import json
from typing import Optional

from core.ports.logger import ILogger
from core.ports.pubsub_client import IPubSubClient

from gateway.adapters.cnc.parsers.grblMsgTypes import GRBL_MSG_STATUS

# Constants
PUBSUB_CHANNEL = "grbl_messages"
LOG_LEVELS = ["critical", "error", "warning", "info", "debug"]


class GrblMonitor:
    def __init__(self, logger: ILogger, pubsub_client: IPubSubClient):
        # Configure logger
        self.logger = logger

        # PubSub client for publishing updates to external apps
        self.pubsub_client = pubsub_client

    # LOGGER

    def debug(self, log: str, queue: bool = False):
        self.logger.debug(log)

    def info(self, log: str, queue: bool = False):
        self.logger.info(log)

    def warning(self, log: str, queue: bool = False):
        self.logger.warning(log)

    def error(self, log: str, queue: bool = False):
        self.logger.error(log)

    def critical(self, log: str, exc_info: bool = True, queue: bool = False):
        self.logger.critical(log, exc_info=exc_info)

    def sent(self, command: str, debug: bool = False):
        command = command.strip()  # Strip all EOL characters for consistency
        if debug:
            self.logger.debug("[Sent] command: {}".format(command))
            return
        self.logger.info("[Sent] command: {}".format(command))

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

        # Publish in PubSub
        self._publish("received", message)

    # PUBSUB

    def _publish(self, msgType: str, message: str):
        pubsub_message = json.dumps({"type": msgType, "message": message})
        self.pubsub_client.publish(PUBSUB_CHANNEL, pubsub_message)
