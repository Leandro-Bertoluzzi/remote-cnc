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
from functools import partial
from typing import Callable

import redis
from core.config import (
    FILES_FOLDER_PATH,
    GRBL_SIMULATION,
    REDIS_DB_STORAGE,
    REDIS_HOST,
    REDIS_PORT,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
)
from core.domain.gateway import (
    GW_STATE_FILE_EXECUTION,
    GW_STATE_IDLE,
    GW_STATE_STREAMING,
)
from core.ports.logger import ILogger
from infrastructure.file_storage import FileSystemStorage
from infrastructure.logging.logger_factory import setup_combined_logger, setup_stream_logger

from gateway.adapters.cnc.controller import GrblController
from gateway.adapters.serial import SerialService
from gateway.application.command_processor import CommandProcessor
from gateway.application.file_executor import FileExecutor
from gateway.application.session_manager import SessionManager
from gateway.application.status_publisher import StatusPublisher

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
# Internal
# ---------------------------------------------------------------------------


def _file_executor_logger_factory(
    logger: logging.Logger, additional_logger_name: str | None
) -> tuple[logging.Logger, Callable[[], None]]:
    """Factory for the FileExecutor's logger.

    If *additional_logger_name* is given, a ``FileHandler``  is attached so
    that execution events are appended to a shared logs file.

    Returns a tuple of (logger, cleanup_fn), where *cleanup_fn* should be called by
    the caller to close the handler when the task is done.
    """
    if additional_logger_name:
        combined_logger, handler = setup_combined_logger(logger, additional_logger_name)

        def _cleanup() -> None:
            handler.close()
            combined_logger.removeHandler(handler)

        return combined_logger, _cleanup

    return logger, lambda: None


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_shutdown_requested = False


def _signal_handler(signum, frame, logger: ILogger) -> None:
    global _shutdown_requested
    logger.info("Shutdown signal received (%s)", signal.Signals(signum).name)
    _shutdown_requested = True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def create_gateway(
    serial_port: str,
    serial_baudrate: int,
    logger: ILogger,
) -> tuple[GrblController, CommandProcessor, StatusPublisher, FileExecutor, SessionManager]:
    """Wire up all Gateway components and return them."""
    redis_conn = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE,
    )

    # GrblController — the serial owner
    serial_adapter = SerialService()
    controller = GrblController(
        serial=serial_adapter,
        logger=setup_stream_logger("controller", logging.INFO),
        pubsub_client=redis_conn,
        skip_startup_validation=GRBL_SIMULATION,
    )

    def file_executor_logger_factory(
        additional_logger_name: str | None,
    ) -> tuple[logging.Logger, Callable[[], None]]:
        return _file_executor_logger_factory(logger, additional_logger_name)

    # Sub-systems
    session_manager = SessionManager(pubsub_client=redis_conn, store=redis_conn, logger=logger)
    file_executor = FileExecutor(
        controller,
        pubsub_client=redis_conn,
        storage=FileSystemStorage(FILES_FOLDER_PATH),
        logger_factory=file_executor_logger_factory,
    )
    status_publisher = StatusPublisher(
        controller,
        session_manager,
        file_executor,
        store=redis_conn,
        pubsub_client=redis_conn,
    )
    command_processor = CommandProcessor(
        controller,
        session_manager,
        file_executor,
        command_queue=redis_conn,
        logger=logger,
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
    logger: ILogger,
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
            controller.query_status_report()
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
                "[Gateway] buffer_fill=%.1f%%, file_running=%s, serial_alive=%s",
                controller.get_buffer_fill(),
                file_executor.is_running,
                serial_alive,
            )
            last_pipeline_summary = now


def shutdown(
    controller: GrblController,
    status_publisher: StatusPublisher,
    logger: ILogger,
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

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, partial(_signal_handler, logger=gateway_logger))
    signal.signal(signal.SIGTERM, partial(_signal_handler, logger=gateway_logger))

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
