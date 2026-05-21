"""Tests for GrblInitializer."""

import logging
from unittest.mock import MagicMock

import pytest
from adapters.cnc.fakes import FakeSerial
from gateway.adapters.cnc.communicator import GrblCommunicator
from gateway.adapters.cnc.initializer import GrblInitializer
from gateway.adapters.cnc.line_parser import GrblLineParser
from gateway.adapters.cnc.monitor import GrblMonitor
from gateway.adapters.cnc.parsers.grblMsgTypes import (
    GRBL_MSG_FEEDBACK,
    GRBL_MSG_STARTUP,
    GRBL_RESULT_OK,
)
from gateway.adapters.cnc.status import GrblStatus
from pytest_mock.plugin import MockerFixture
from serial import SerialException


class TestGrblInitializer:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        grbl_logger = logging.getLogger("test_logger")
        self.serial = FakeSerial()
        self.grbl_status = GrblStatus()
        self.grbl_monitor = GrblMonitor(grbl_logger, redis_conn=MagicMock())

        # Silence all monitor output
        mocker.patch.object(GrblMonitor, "debug")
        mocker.patch.object(GrblMonitor, "info")
        mocker.patch.object(GrblMonitor, "warning")
        mocker.patch.object(GrblMonitor, "error")
        mocker.patch.object(GrblMonitor, "critical")
        mocker.patch.object(GrblMonitor, "sent")
        mocker.patch.object(GrblMonitor, "received")

        self.initializer = GrblInitializer(
            serial=self.serial,
            monitor=self.grbl_monitor,
        )

    def _make_communicator(self, mocker: MockerFixture) -> GrblCommunicator:
        """Returns a stopped GrblCommunicator suitable for receiving send() calls."""
        return GrblCommunicator(
            serial=self.serial,
            grbl_status=self.grbl_status,
            monitor=self.grbl_monitor,
            on_ok=mocker.MagicMock(),
            on_error=mocker.MagicMock(),
            on_alarm=mocker.MagicMock(),
            on_message=mocker.MagicMock(),
            on_disconnect=mocker.MagicMock(),
        )

    # ------------------------------------------------------------------ #
    # open_connection                                                      #
    # ------------------------------------------------------------------ #

    def test_open_connection_ok(self, mocker: MockerFixture):
        """A valid GRBL_MSG_STARTUP banner returns the parsed payload."""
        self.serial.start_return = "Grbl 1.1h"
        mocker.patch.object(
            GrblLineParser,
            "parse",
            return_value=(
                GRBL_MSG_STARTUP,
                {"firmware": "Grbl", "version": "1.1h", "message": None, "raw": "Grbl 1.1h"},
            ),
        )

        payload = self.initializer.open_connection("/dev/ttyUSB0", 115200, 0.1)

        assert payload["firmware"] == "Grbl"
        assert payload["version"] == "1.1h"

    def test_open_connection_wrong_msg_type_raises(self, mocker: MockerFixture):
        """A non-startup banner raises an exception with a clear message."""
        self.serial.start_return = "ok"
        mocker.patch.object(GrblLineParser, "parse", return_value=(GRBL_RESULT_OK, {}))

        with pytest.raises(Exception) as exc_info:
            self.initializer.open_connection("/dev/ttyUSB0", 115200, 0.1)

        assert "Failed starting connection with GRBL" in str(exc_info.value)

    def test_open_connection_serial_error_propagates(self, mocker: MockerFixture):
        """A SerialException from startConnection propagates."""
        self.serial.start_side_effect = SerialException("port closed")

        with pytest.raises(SerialException):
            self.initializer.open_connection("/dev/ttyUSB0", 115200, 0.1)

    def test_open_connection_skip_validation(self, mocker: MockerFixture):
        """With skip_startup_validation=True, any banner message type is accepted."""
        initializer = GrblInitializer(
            serial=self.serial,
            monitor=self.grbl_monitor,
            skip_startup_validation=True,
        )
        self.serial.start_return = "simulator ready"
        mocker.patch.object(GrblLineParser, "parse", return_value=("UNKNOWN_TYPE", {"foo": "bar"}))

        # Should not raise
        payload = initializer.open_connection("/dev/ttyUSB0", 115200, 0.1)
        assert payload == {"foo": "bar"}

    # ------------------------------------------------------------------ #
    # handle_post_startup                                                  #
    # ------------------------------------------------------------------ #

    def test_handle_post_startup_no_homing_message(self, mocker: MockerFixture):
        """A plain 'ok' after startup does not trigger the homing callback."""
        comm = self._make_communicator(mocker)
        mock_callback = mocker.MagicMock()
        initializer = GrblInitializer(
            serial=self.serial,
            monitor=self.grbl_monitor,
            on_homing_required=mock_callback,
        )

        self.serial.lines = ["ok"]
        mocker.patch.object(GrblLineParser, "parse", return_value=(GRBL_RESULT_OK, {}))

        initializer.handle_post_startup(comm)

        mock_callback.assert_not_called()
        assert comm.queue.empty()

    def test_handle_post_startup_homing_with_callback(self, mocker: MockerFixture):
        """When the homing message is detected and a callback is set, it is called."""
        comm = self._make_communicator(mocker)
        mock_callback = mocker.MagicMock()
        initializer = GrblInitializer(
            serial=self.serial,
            monitor=self.grbl_monitor,
            on_homing_required=mock_callback,
        )

        self.serial.lines = ["[MSG:'$H'|'$X' to unlock]"]
        mocker.patch.object(
            GrblLineParser,
            "parse",
            return_value=(
                GRBL_MSG_FEEDBACK,
                {"message": "'$H'|'$X' to unlock", "raw": "[MSG:'$H'|'$X' to unlock]"},
            ),
        )

        initializer.handle_post_startup(comm)

        mock_callback.assert_called_once()
        # Default $X enqueue should NOT happen when a callback is present
        assert comm.queue.empty()

    def test_handle_post_startup_homing_no_callback_enqueues_disable_alarm(
        self, mocker: MockerFixture
    ):
        """Without a callback, the default handler enqueues '$X' (disable alarm)."""
        comm = self._make_communicator(mocker)

        self.serial.lines = ["[MSG:'$H'|'$X' to unlock]"]
        mocker.patch.object(
            GrblLineParser,
            "parse",
            return_value=(
                GRBL_MSG_FEEDBACK,
                {"message": "'$H'|'$X' to unlock", "raw": "[MSG:'$H'|'$X' to unlock]"},
            ),
        )

        self.initializer.handle_post_startup(comm)

        assert not comm.queue.empty()
        assert comm.queue.get_nowait() == "$X"

    def test_handle_post_startup_serial_error_does_not_crash(self, mocker: MockerFixture):
        """A SerialException during the post-startup read is caught and logged."""
        comm = self._make_communicator(mocker)
        self.serial.read_line_side_effect = SerialException("port closed")
        mock_critical = mocker.patch.object(GrblMonitor, "critical")

        # Should not raise
        self.initializer.handle_post_startup(comm)

        mock_critical.assert_called_once()
        assert comm.queue.empty()

    # ------------------------------------------------------------------ #
    # queue_initial_queries                                                #
    # ------------------------------------------------------------------ #

    def test_queue_initial_queries_enqueues_build_parser_settings(self, mocker: MockerFixture):
        """queue_initial_queries sends $I, $G, $$ to the communicator in that order."""
        comm = self._make_communicator(mocker)

        self.initializer.queue_initial_queries(comm)

        commands = []
        while not comm.queue.empty():
            commands.append(comm.queue.get_nowait())

        assert commands == ["$I", "$G", "$$"]
