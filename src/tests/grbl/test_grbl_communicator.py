"""Tests for GrblCommunicator"""

import logging
import threading
from queue import Queue

import pytest
from core.utilities.grbl.grblCommunicator import GRBL_QUERY_COMMANDS, GrblCommunicator
from core.utilities.grbl.grblMonitor import GrblMonitor
from core.utilities.grbl.grblStatus import GrblStatus
from core.utilities.serial import SerialService
from pytest_mock.plugin import MockerFixture
from serial import SerialException


class TestGrblCommunicator:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        grbl_logger = logging.getLogger("test_logger")
        self.grbl_status = GrblStatus()
        self.grbl_monitor = GrblMonitor(grbl_logger)

        # Callbacks
        self.mock_on_ok = mocker.MagicMock()
        self.mock_on_error = mocker.MagicMock()
        self.mock_on_alarm = mocker.MagicMock()
        self.mock_on_message = mocker.MagicMock()
        self.mock_on_program_end = mocker.MagicMock()
        self.mock_on_disconnect = mocker.MagicMock()

        self.communicator = GrblCommunicator(
            serial=SerialService(),
            grbl_status=self.grbl_status,
            monitor=self.grbl_monitor,
            on_ok=self.mock_on_ok,
            on_error=self.mock_on_error,
            on_alarm=self.mock_on_alarm,
            on_message=self.mock_on_message,
            on_program_end=self.mock_on_program_end,
            on_disconnect=self.mock_on_disconnect,
        )

        # Mock logger methods
        mocker.patch.object(GrblMonitor, "debug")
        mocker.patch.object(GrblMonitor, "info")
        mocker.patch.object(GrblMonitor, "warning")
        mocker.patch.object(GrblMonitor, "error")
        mocker.patch.object(GrblMonitor, "critical")
        mocker.patch.object(GrblMonitor, "sent")
        mocker.patch.object(GrblMonitor, "received")

    # ------------------------------------------------------------------ #
    # Public API methods                                                 #
    # ------------------------------------------------------------------ #
    def test_request_status_query(self, mocker: MockerFixture):
        self.communicator.request_status_query()

        assert self.communicator._status_query_pending is True

    def test_request_status_query_idempotent(self, mocker: MockerFixture):
        self.communicator.request_status_query()
        self.communicator.request_status_query()

        assert self.communicator._status_query_pending is True

    # ------------------------------------------------------------------ #
    # serial_io: basic loop                                              #
    # ------------------------------------------------------------------ #

    @pytest.mark.parametrize("paused", [True, False])
    def test_serial_io(self, mocker: MockerFixture, paused):
        # **Test case description (no pause)**
        # Round 1: get command to send + read line + parse line + send command
        # Round 2: get command to send + send command
        # Round 3: read line (no response) — then thread stops

        # Activate the thread handle so the loop runs
        self.communicator._thread = threading.Thread()

        # Mock queue contents
        self.communicator.queue.put("Command 1")
        self.communicator.queue.put("Command 2")

        # Stop the thread after 3 iterations via the ``waiting`` side-effect.
        self._iter = 0
        waiting_values = [True, False, True]

        def waiting_and_stop():
            val = waiting_values[self._iter]
            self._iter += 1
            if self._iter >= len(waiting_values):
                self.communicator._thread = None
            return val

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=paused)

        # Mock serial methods
        mock_serial_waiting = mocker.patch.object(
            SerialService, "waiting", side_effect=waiting_and_stop
        )
        mock_serial_read_line = mocker.patch.object(
            SerialService, "readLine", side_effect=["test message", "", ""]
        )
        mock_serial_send_line = mocker.patch.object(SerialService, "sendLine")

        # Mock monitor methods
        mock_monitor_sent = mocker.patch.object(GrblMonitor, "sent")

        # Spy queue methods
        spy_queue_size = mocker.spy(Queue, "qsize")
        spy_queue_get = mocker.spy(Queue, "get_nowait")

        # Call method under test
        self.communicator._serial_io()

        # **Read serial section**
        assert mock_serial_waiting.call_count == 3
        assert mock_serial_read_line.call_count == (3 if paused else 2)
        # A non-empty response was received once — GrblLineParser processes it
        # and dispatches to on_message (since "test message" is not ok/error/alarm)
        assert self.mock_on_message.call_count == 1
        # **Write serial section**
        # qsize() is always called (peek happens before the paused check),
        # so the count is 3 regardless of pause state.
        assert spy_queue_size.call_count == 3
        assert spy_queue_get.call_count == (0 if paused else 2)
        assert mock_serial_send_line.call_count == (0 if paused else 2)
        assert mock_monitor_sent.call_count == (0 if paused else 2)

    @pytest.mark.parametrize("error_read,error_send", [(True, False), (False, True)])
    def test_serial_io_serial_error(self, mocker: MockerFixture, error_read, error_send):
        self.communicator._thread = threading.Thread()

        # Mock queue contents
        self.communicator.queue.put("Command")

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", return_value=error_read)
        mock_serial_read_line = mocker.patch.object(
            SerialService, "readLine", side_effect=SerialException("mocked-error")
        )
        mock_serial_send_line = mocker.patch.object(
            SerialService, "sendLine", side_effect=SerialException("mocked-error")
        )

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Mock monitor methods
        mock_monitor_error = mocker.patch.object(GrblMonitor, "error")

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        assert mock_serial_read_line.call_count == (1 if error_read else 0)
        assert mock_serial_send_line.call_count == (1 if error_send else 0)
        # On serial error the I/O thread exits without processing any GRBL response
        assert self.mock_on_ok.call_count == 0
        assert self.mock_on_error.call_count == 0
        assert mock_monitor_error.call_count == 1
        assert self.mock_on_disconnect.call_count == 1
        assert self.communicator.alive is False

    def test_serial_io_stop(self, mocker: MockerFixture):
        self.communicator._thread = threading.Thread()
        self.grbl_status._flags["stop"] = True

        # Stop the thread from within empty_queue
        def stop_thread():
            self.communicator._thread = None

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", return_value=False)
        mocker.patch.object(SerialService, "readLine", return_value="")

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Patch empty_queue to stop the loop
        mocker.patch.object(GrblCommunicator, "empty_queue", side_effect=stop_thread)
        mock_monitor_info = mocker.patch.object(GrblMonitor, "info")

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        assert mock_monitor_info.call_count == 3  # started + STOP processed + exiting
        assert self.grbl_status._flags["stop"] is False
        assert self.communicator.alive is False

    def test_serial_io_query_buffer_full(self, mocker: MockerFixture):
        self.communicator._thread = threading.Thread()

        # Mock queue contents
        self.communicator.queue.put("Command 1")

        def stop_thread():
            self.communicator._thread = None
            return False

        # Mock builtin 'sum' function — pretend buffer is full
        mock_sum = mocker.patch("builtins.sum", return_value=500)

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", side_effect=stop_thread)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mock_send_line = mocker.patch.object(SerialService, "sendLine")

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        assert mock_sum.call_count == 3  # if-condition + elif-debug + finally
        assert mock_send_line.call_count == 0

    def test_serial_io_end_command(self, mocker: MockerFixture):
        self.communicator._thread = threading.Thread()

        # Mock queue contents
        self.communicator.queue.put("Command 1")
        self.communicator.queue.put("M30")

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", return_value=False)
        mock_serial_send_line = mocker.patch.object(SerialService, "sendLine")

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Mock monitor methods
        mock_monitor_info = mocker.patch.object(GrblMonitor, "info")

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        assert mock_serial_send_line.call_count == 2
        assert mock_monitor_info.call_count == 3  # started + end cmd + exiting
        mock_monitor_info.assert_any_call("A program end command was found: M30")
        assert self.grbl_status._flags["finished"] is True
        assert self.communicator.alive is False

    # ------------------------------------------------------------------ #
    # Buffer management                                                  #
    # ------------------------------------------------------------------ #

    def test_cline_includes_newline_byte(self, mocker: MockerFixture):
        """Verify that ``cline`` accounts for the '\\n' appended by ``sendLine``."""
        self.communicator._thread = threading.Thread()

        # Use a command with a known length
        command = "G1 X10 Y20"  # 10 chars → 11 bytes with '\n'
        self.communicator.queue.put(command)

        def stop_thread():
            self.communicator._thread = None
            return False

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", side_effect=stop_thread)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mock_send_line = mocker.patch.object(SerialService, "sendLine")

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        assert mock_send_line.call_count == 1
        # _sumcline must equal len("G1 X10 Y20") + 1 (for '\n') = 11
        assert self.communicator._sumcline == len(command) + 1

    def test_buffer_will_not_overflow_rx_buffer(self, mocker: MockerFixture):
        """Verify that serial_io respects ``RX_BUFFER_SIZE`` including the '\\n' byte.

        Queue several commands whose combined sizes (with '\\n') exceed 128 bytes.
        Only the ones that fit should be sent.
        """
        from core.utilities.grbl.grblCommunicator import RX_BUFFER_SIZE

        self.communicator._thread = threading.Thread()

        # Each command is 20 chars → 21 bytes with '\n'.
        # 128 / 21 = 6.09 → only 6 commands fit (126 bytes).
        command = "G1 X100.000 Y200.000"
        assert len(command) == 20
        for _ in range(8):
            self.communicator.queue.put(command)

        sent_commands: list[str] = []

        def record_send(cmd):
            sent_commands.append(cmd)

        self._loop_count = 0

        def waiting_side_effect():
            self._loop_count += 1
            if self._loop_count > 20:
                self.communicator._thread = None
            return False

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", side_effect=waiting_side_effect)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(SerialService, "sendLine", side_effect=record_send)

        # Mock status methods
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        # Call method under test
        self.communicator._serial_io()

        # Assertions
        # Only 6 commands should fit: 6 * 21 = 126 ≤ 128, but 7 * 21 = 147 > 128
        assert len(sent_commands) == 6
        assert self.communicator._sumcline <= RX_BUFFER_SIZE

    def test_serial_io_alive_flag(self, mocker: MockerFixture):
        """``alive`` is True during execution and False after exit."""
        self.communicator._thread = threading.Thread()

        alive_during: list[bool] = []

        def capture_alive():
            alive_during.append(self.communicator.alive)
            self.communicator._thread = None
            return False

        # Mock serial methods
        mocker.patch.object(SerialService, "waiting", side_effect=capture_alive)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        assert self.communicator.alive is False
        self.communicator._serial_io()

        assert alive_during == [True]
        assert self.communicator.alive is False

    def test_serial_io_catches_unhandled_exception(self, mocker: MockerFixture):
        """An unexpected exception in one iteration is caught and logged, but the
        loop keeps running.  ``alive`` must be False only after the
        thread finally exits."""
        self.communicator._thread = threading.Thread()

        call_count = 0

        def raise_once_then_stop():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("boom")
            # Second call: stop the loop cleanly
            self.communicator._thread = None
            return False

        mocker.patch.object(SerialService, "waiting", side_effect=raise_once_then_stop)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(GrblStatus, "paused", return_value=False)
        mock_critical = mocker.patch.object(GrblMonitor, "critical")

        self.communicator._serial_io()

        # Loop must have continued after the exception (waiting called twice)
        assert call_count == 2
        assert self.communicator.alive is False
        mock_critical.assert_called_once()
        assert "boom" in mock_critical.call_args[0][0]

    def test_serial_io_flushes_status_query_flag(self, mocker: MockerFixture):
        """When ``_status_query_pending`` is True, serial_io sends '?' via
        sendBytes and clears the flag before processing other I/O."""
        self.communicator._thread = threading.Thread()
        self.communicator._status_query_pending = True

        sent_bytes: list[bytes] = []

        def capture_and_stop(code: bytes):
            sent_bytes.append(code)
            # Stop the loop after the first sendBytes call
            self.communicator._thread = None

        mocker.patch.object(SerialService, "sendBytes", side_effect=capture_and_stop)
        mocker.patch.object(SerialService, "waiting", return_value=False)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(GrblStatus, "paused", return_value=False)

        self.communicator._serial_io()

        assert b"?" in sent_bytes
        assert self.communicator._status_query_pending is False

    def test_serial_io_status_query_serial_error_clears_flag(self, mocker: MockerFixture):
        """If sendBytes raises SerialException while sending '?', the flag is
        still cleared and serial_io does not crash."""
        self.communicator._thread = threading.Thread()
        self.communicator._status_query_pending = True

        call_count = 0

        def raise_then_stop(code: bytes):
            nonlocal call_count
            call_count += 1
            self.communicator._thread = None
            raise SerialException("port error")

        mocker.patch.object(SerialService, "sendBytes", side_effect=raise_then_stop)
        mocker.patch.object(SerialService, "waiting", return_value=False)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(GrblStatus, "paused", return_value=False)
        mock_error = mocker.patch.object(GrblMonitor, "error")

        self.communicator._serial_io()

        assert self.communicator._status_query_pending is False
        assert call_count == 1
        mock_error.assert_called_once()

    # ------------------------------------------------------------------ #
    # Query commands bypass pause                                          #
    # ------------------------------------------------------------------ #

    def test_serial_io_query_command_bypasses_pause(self, mocker: MockerFixture):
        """A query command (e.g. '$G') is sent even when the controller is paused."""
        self.communicator._thread = threading.Thread()
        self.communicator.queue.put("$G")

        sent_commands: list[str] = []

        def record_and_stop(cmd: str):
            sent_commands.append(cmd)
            self.communicator._thread = None

        mocker.patch.object(GrblStatus, "paused", return_value=True)
        mocker.patch.object(SerialService, "waiting", return_value=False)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(SerialService, "sendLine", side_effect=record_and_stop)

        self.communicator._serial_io()

        assert sent_commands == ["$G"]
        assert "$G" in GRBL_QUERY_COMMANDS  # sanity check

    def test_serial_io_motion_command_blocked_when_paused(self, mocker: MockerFixture):
        """A motion command is NOT sent when the controller is paused."""
        self.communicator._thread = threading.Thread()
        self.communicator.queue.put("G0 X10")

        self._iter = 0

        def stop_after_three():
            self._iter += 1
            if self._iter >= 3:
                self.communicator._thread = None
            return False

        mocker.patch.object(GrblStatus, "paused", return_value=True)
        mocker.patch.object(SerialService, "waiting", side_effect=stop_after_three)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mock_send = mocker.patch.object(SerialService, "sendLine")

        self.communicator._serial_io()

        assert mock_send.call_count == 0
        # The motion command must still be in the queue (not consumed)
        assert self.communicator.queue.qsize() == 1

    def test_serial_io_query_passes_motion_blocked_when_paused(self, mocker: MockerFixture):
        """With paused=True, a motion command at the head of the queue blocks
        subsequent queries — FIFO is preserved and the peek sees the motion command."""
        self.communicator._thread = threading.Thread()
        # Motion command is first; query is behind it
        self.communicator.queue.put("G0 X10")
        self.communicator.queue.put("$G")

        self._iter = 0

        def stop_after_three():
            self._iter += 1
            if self._iter >= 3:
                self.communicator._thread = None
            return False

        mocker.patch.object(GrblStatus, "paused", return_value=True)
        mocker.patch.object(SerialService, "waiting", side_effect=stop_after_three)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mock_send = mocker.patch.object(SerialService, "sendLine")

        self.communicator._serial_io()

        # Neither command should have been sent: the motion command blocks the whole queue
        assert mock_send.call_count == 0
        assert self.communicator.queue.qsize() == 2

    # ------------------------------------------------------------------ #
    # EEPROM single-step mode                                            #
    # ------------------------------------------------------------------ #

    def test_eeprom_single_step_blocks_next_command(self, mocker: MockerFixture):
        """After sending an EEPROM-writing command, ``_serial_io`` must NOT dequeue
        the next command until GRBL has acknowledged the previous one (i.e., until
        ``cline`` is empty). This prevents corruption of GRBL's internal EEPROM state.

        Scenario
        --------
        Queue: ["$$", "G0 X10"]

        Round 1  — dequeue & stage "$$", send it  → cline=[3], single_step=True
        Round 2  — buffer not empty (cline=[3]), single_step=True  → "G0 X10" must NOT be
                   dequeued.  Loop stops here (waiting returns False  → thread=None).

        Expected: only 1 sendLine call ("$$"), "G0 X10" remains in the queue.
        """
        self.communicator._thread = threading.Thread()

        # “$$” is in _EEPROM_PATTERN, so single-step will be engaged after it is sent.
        self.communicator.queue.put("$$")
        self.communicator.queue.put("G0 X10")

        sent_commands: list[str] = []

        call_count = 0

        def record_and_stop(cmd: str):
            sent_commands.append(cmd)

        def waiting_side_effect():
            nonlocal call_count
            call_count += 1
            # Stop the loop after a few iterations so the test terminates.
            if call_count >= 5:
                self.communicator._thread = None
            return False

        mocker.patch.object(GrblStatus, "paused", return_value=False)
        mocker.patch.object(SerialService, "waiting", side_effect=waiting_side_effect)
        mocker.patch.object(SerialService, "readLine", return_value="")
        mocker.patch.object(SerialService, "sendLine", side_effect=record_and_stop)

        self.communicator._serial_io()

        # Only "$$" should have been sent; "G0 X10" must still be in the queue.
        assert sent_commands == ["$$"]
        assert self.communicator.queue.qsize() == 1
        assert self.communicator.queue.queue[0] == "G0 X10"
        assert self.communicator._single_step is True

    # ------------------------------------------------------------------ #
    # _handle_response: semantic dispatch and buffer accounting          #
    # ------------------------------------------------------------------ #

    def test_handle_response_ok_drains_cline_sline(self):
        """``ok`` removes the first cline/sline entry and calls on_ok with done_cmd."""
        cline = [4, 6, 8]
        sline = ["G0 X10", "G1 Y20", "G28"]

        self.communicator._handle_response("ok", cline, sline)

        # First entry drained
        assert cline == [6, 8]
        assert sline == ["G1 Y20", "G28"]
        # on_ok called with the consumed command
        self.mock_on_ok.assert_called_once_with("G0 X10")
        # No error or alarm callbacks
        self.mock_on_error.assert_not_called()
        self.mock_on_alarm.assert_not_called()

    def test_handle_response_ok_updates_sumcline(self):
        """``_sumcline`` reflects the remaining cline bytes after an ok."""
        cline = [10, 20, 30]
        sline = ["A", "B", "C"]

        self.communicator._handle_response("ok", cline, sline)

        assert self.communicator._sumcline == 50  # sum([20, 30])

    def test_handle_response_error_clears_buffers_and_queue(self):
        """``error:N`` clears cline/sline, resets _sumcline to 0, drains the queue,
        and calls on_error with (error_line, clean_payload)."""
        cline = [4, 6]
        sline = ["bad cmd", "G90"]
        self.communicator.queue.put("pending 1")
        self.communicator.queue.put("pending 2")

        self.communicator._handle_response("error:25", cline, sline)

        assert cline == []
        assert sline == []
        assert self.communicator._sumcline == 0
        assert self.communicator.queue.empty()
        # on_error receives (first sline element, payload without 'raw')
        self.mock_on_error.assert_called_once()
        error_line, payload = self.mock_on_error.call_args[0]
        assert error_line == "bad cmd"
        assert "raw" not in payload
        assert payload["code"] == 25

    def test_handle_response_error_resets_sumcline(self):
        """``_sumcline`` is 0 after an error response regardless of prior value."""
        self.communicator._sumcline = 99
        cline = [10, 20]
        sline = ["cmd", "other"]

        self.communicator._handle_response("error:1", cline, sline)

        assert self.communicator._sumcline == 0

    def test_handle_response_alarm_clears_buffers_and_sets_flags(self):
        """``ALARM:N`` clears buffers, sets ALARM and PAUSED flags, and calls on_alarm."""
        cline = [5, 3]
        sline = ["$H", "G54"]

        self.communicator._handle_response("ALARM:6", cline, sline)

        assert cline == []
        assert sline == []
        assert self.communicator._sumcline == 0
        self.mock_on_alarm.assert_called_once()
        alarm_line, payload = self.mock_on_alarm.call_args[0]
        assert alarm_line == "$H"
        assert "raw" not in payload
        assert payload["code"] == 6

    def test_handle_response_message_forwarded_to_on_message(self):
        """Non-ack messages are stripped of 'raw' and forwarded to on_message."""
        cline: list[int] = []
        sline: list[str] = []

        self.communicator._handle_response("<Idle|MPos:0.0,0.0,0.0>", cline, sline)

        self.mock_on_ok.assert_not_called()
        self.mock_on_error.assert_not_called()
        self.mock_on_alarm.assert_not_called()
        self.mock_on_message.assert_called_once()
        msg_type, payload = self.mock_on_message.call_args[0]
        assert "raw" not in payload
        assert msg_type is not None

    def test_handle_response_parse_error_does_not_raise(self, mocker: MockerFixture):
        """If GrblLineParser raises, _handle_response logs and returns without calling
        any callback."""
        from core.utilities.grbl.grblLineParser import GrblLineParser

        mocker.patch.object(GrblLineParser, "parse", side_effect=ValueError("bad line"))
        mock_error = mocker.patch.object(GrblMonitor, "error")

        self.communicator._handle_response("not valid", [], [])

        mock_error.assert_called_once()
        self.mock_on_ok.assert_not_called()
        self.mock_on_message.assert_not_called()
