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
import time

import redis
from core.config import (
    GRBL_SIMULATION,
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
# Polling intervals
# ---------------------------------------------------------------------------

# How often to send a status report query (seconds)
STATUS_POLL_INTERVAL = 0.125
# How often to send a parser-state query (seconds)
PARSER_STATE_POLL_INTERVAL = 10
# BLPOP timeout when a file is being executed (seconds)
FILE_EXEC_BLPOP_TIMEOUT = 0.1
# How often to log a pipeline-health summary (seconds)
PIPELINE_SUMMARY_INTERVAL = 5.0

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
    logger: logging.Logger,
) -> tuple[GrblController, CommandProcessor, StatusPublisher, FileExecutor, SessionManager]:
    """Wire up all Gateway components and return them."""
    redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE,
    )

    # GrblController — the serial owner
    grbl_logger = setup_stream_logger("controller", logging.INFO)
    controller = GrblController(logger=grbl_logger, skip_startup_validation=GRBL_SIMULATION)

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
    logger: logging.Logger,
) -> None:
    """Main event-loop of the Gateway.

    1. Poll GRBL status (``?``) and parser state (``$G``) periodically.
    2. Process one command from the priority queues.
    3. Tick the file executor (sends one G-code line if due).
    4. Publish CNC status if the interval has elapsed.
    5. Update the gateway state label.
    """
    logger.info("CNC Gateway is running.  Waiting for commands…")

    last_status_poll = time.time()
    last_parser_state_poll = time.time()
    last_pipeline_summary = time.time()

    while not _shutdown_requested:
        now = time.time()

        # 0. Check serial thread health
        if not controller.is_io_alive():
            logger.critical("serial_io thread is dead! Aborting gateway loop.")
            break

        # 1. Periodic GRBL queries
        if now - last_status_poll >= STATUS_POLL_INTERVAL:
            controller.queryStatusReport()
            last_status_poll = now

        if now - last_parser_state_poll >= PARSER_STATE_POLL_INTERVAL:
            controller.query_gcode_parser_state()
            last_parser_state_poll = now

        # 2. Process commands — use a short timeout during file execution
        # so that tick() is called frequently enough.
        blpop_timeout = FILE_EXEC_BLPOP_TIMEOUT if file_executor.is_running else None
        command_processor.process_one(timeout=blpop_timeout)

        if command_processor.should_stop:
            logger.info("Disconnect requested, shutting down…")
            break

        # 3. File execution tick
        file_executor.tick()

        # 4. Publish status
        status_publisher.publish_if_due()

        # 5. Update gateway state
        if file_executor.is_running:
            status_publisher.gateway_state = GW_STATE_FILE_EXECUTION
        elif session_manager.has_active_session():
            status_publisher.gateway_state = GW_STATE_STREAMING
        else:
            status_publisher.gateway_state = GW_STATE_IDLE

        # 6. Periodic pipeline-health summary
        if now - last_pipeline_summary >= PIPELINE_SUMMARY_INTERVAL:
            serial_alive = controller.is_io_alive()
            logger.info(
                "[Gateway] buffer_fill=%.1f%%, "
                "commands_count=%d, file_running=%s, serial_alive=%s",
                controller.get_buffer_fill(),
                controller.commands_count,
                file_executor.is_running,
                serial_alive,
            )
            last_pipeline_summary = now


def shutdown(
    controller: GrblController,
    status_publisher: StatusPublisher,
    logger: logging.Logger,
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

    gateway_logger = setup_stream_logger("gateway", logging.INFO)

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
            create_gateway(args.port, args.baudrate, gateway_logger)
        )
        run_gateway(
            controller,
            command_processor,
            status_publisher,
            file_executor,
            session_manager,
            gateway_logger,
        )
    except KeyboardInterrupt:
        gateway_logger.info("KeyboardInterrupt received")
    except Exception:
        gateway_logger.critical("Fatal error in CNC Gateway", exc_info=True)
        sys.exit(1)
    finally:
        if controller is not None and status_publisher is not None:
            shutdown(controller, status_publisher, gateway_logger)


if __name__ == "__main__":
    main()
