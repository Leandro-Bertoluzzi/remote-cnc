"""Composition root for the CNC Gateway application."""

from __future__ import annotations

import logging
from typing import Callable

import redis
from core.config import (
    FILES_FOLDER_PATH,
    GRBL_SIMULATION,
    REDIS_DB_STORAGE,
    REDIS_HOST,
    REDIS_PORT,
)
from core.domain.gateway import GW_STATE_IDLE
from core.ports.logger import ILogger
from gateway.adapters.cnc.controller import GrblController
from gateway.adapters.serial import SerialService
from gateway.application.command_processor import CommandProcessor
from gateway.application.file_executor import FileExecutor
from gateway.application.session_manager import SessionManager
from gateway.application.status_publisher import StatusPublisher
from infrastructure.file_storage import FileSystemStorage
from infrastructure.logging.logger_factory import setup_combined_logger, setup_stream_logger


def _file_executor_logger_factory(
    logger: logging.Logger, additional_logger_name: str | None
) -> tuple[logging.Logger, Callable[[], None]]:
    """Factory for the FileExecutor's logger.

    If *additional_logger_name* is given, a ``FileHandler`` is attached so
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


def create_gateway(
    serial_port: str,
    serial_baudrate: int,
    logger: ILogger,
) -> tuple[GrblController, CommandProcessor, StatusPublisher, FileExecutor, SessionManager]:
    """Wire up all Gateway components and connect to the CNC device."""
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
