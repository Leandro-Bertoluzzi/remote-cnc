"""CNC Gateway — main entry point.

A dedicated, always-on process that owns the exclusive serial connection
to the GRBL device. It receives commands from Redis priority queues and
publishes CNC state via Redis PubSub.

Usage::

    python -m gateway.main  # uses SERIAL_PORT / SERIAL_BAUDRATE from env
    python -m gateway.main --port /dev/ttyUSB0 --baudrate 115200

See DR-0001 for the architectural rationale.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys

import redis
from core.config import (
    REDIS_DB_STORAGE,
    REDIS_HOST,
    REDIS_PORT,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
)
from core.utilities.gateway.constants import (
    GW_STATE_FILE_EXECUTION,
    GW_STATE_IDLE,
    GW_STATE_STREAMING,
)
from core.utilities.grbl.grblController import GrblController
from core.utilities.loggerFactory import setup_stream_logger

from gateway.commandProcessor import CommandProcessor
from gateway.fileExecutor import FileExecutor
from gateway.sessionManager import SessionManager
from gateway.statusPublisher import StatusPublisher

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    logger.info("Shutdown signal received (%s)", signal.Signals(signum).name)
    _shutdown_requested = True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def create_gateway(
    serial_port: str,
    serial_baudrate: int,
) -> tuple[GrblController, CommandProcessor, StatusPublisher, FileExecutor, SessionManager]:
    """Wire up all Gateway components and return them."""
    redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE,
    )

    # GrblController — the serial owner
    grbl_logger = setup_stream_logger("gateway", logging.INFO)
    controller = GrblController(logger=grbl_logger)

    # Sub-systems
    session_manager = SessionManager(redis_conn=redis_conn)
    file_executor = FileExecutor(controller, redis_conn=redis_conn)
    status_publisher = StatusPublisher(
        controller,
        session_manager,
        file_executor,
        redis_conn=redis_conn,
    )
    command_processor = CommandProcessor(
        controller,
        session_manager,
        file_executor,
        redis_conn=redis_conn,
    )

    # Connect to the CNC device
    logger.info("Connecting to CNC at %s @ %d …", serial_port, serial_baudrate)
    try:
        response = controller.connect(serial_port, serial_baudrate)
    except Exception:
        logger.critical("Failed to connect to CNC device", exc_info=True)
        raise

    if response is None:
        raise RuntimeError("GrblController.connect() returned None — startup alarm?")

    logger.info("Connected to CNC device: %s", response)
    status_publisher.gateway_state = GW_STATE_IDLE

    return controller, command_processor, status_publisher, file_executor, session_manager


def run_gateway(
    controller: GrblController,
    command_processor: CommandProcessor,
    status_publisher: StatusPublisher,
    file_executor: FileExecutor,
    session_manager: SessionManager,
) -> None:
    """Main event-loop of the Gateway.

    1. Process one command from the priority queues (blocks ≤1 s).
    2. Tick the file executor (sends one G-code line if due).
    3. Publish CNC status if the interval has elapsed.
    4. Update the gateway state label.
    """
    logger.info("CNC Gateway is running.  Waiting for commands…")

    while not _shutdown_requested:
        # 1. Process commands
        command_processor.process_one()

        if command_processor.should_stop:
            logger.info("Disconnect requested, shutting down…")
            break

        # 2. File execution tick
        file_executor.tick()

        # 3. Publish status
        status_publisher.publish_if_due()

        # 4. Update gateway state
        if file_executor.is_running:
            status_publisher.gateway_state = GW_STATE_FILE_EXECUTION
        elif session_manager.has_active_session():
            status_publisher.gateway_state = GW_STATE_STREAMING
        else:
            status_publisher.gateway_state = GW_STATE_IDLE


def shutdown(
    controller: GrblController,
    status_publisher: StatusPublisher,
) -> None:
    """Clean up resources."""
    logger.info("Shutting down CNC Gateway…")

    try:
        status_publisher.cleanup()
    except Exception:
        logger.warning("Error cleaning up status publisher", exc_info=True)

    try:
        controller.disconnect()
    except Exception:
        logger.warning("Error disconnecting from CNC", exc_info=True)

    logger.info("CNC Gateway stopped.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="CNC Gateway — dedicated serial process")
    parser.add_argument("--port", default=SERIAL_PORT, help="Serial port (default: from env)")
    parser.add_argument(
        "--baudrate",
        type=int,
        default=SERIAL_BAUDRATE,
        help="Serial baudrate (default: from env)",
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    controller = None
    status_publisher = None

    try:
        controller, command_processor, status_publisher, file_executor, session_manager = (
            create_gateway(args.port, args.baudrate)
        )
        run_gateway(controller, command_processor, status_publisher, file_executor, session_manager)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    except Exception:
        logger.critical("Fatal error in CNC Gateway", exc_info=True)
        sys.exit(1)
    finally:
        if controller is not None and status_publisher is not None:
            shutdown(controller, status_publisher)


if __name__ == "__main__":
    main()
