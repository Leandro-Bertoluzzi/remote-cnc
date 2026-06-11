"""Tests for gateway.FileExecutor."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
from core.domain.gateway import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENT_FILE_STARTED,
    EVENTS_CHANNEL,
)
from fakes import FakeController, FakeFileStorage
from gateway.application.file_executor import FileExecutor


def make_executor(
    controller: Optional[FakeController] = None,
    pubsub_client: Optional[MagicMock] = None,
) -> tuple[FileExecutor, FakeController, MagicMock]:
    ctrl = controller or FakeController()
    pubsub_mock = pubsub_client or MagicMock()
    executor = FileExecutor(
        ctrl,
        pubsub_client=pubsub_mock,
        storage=FakeFileStorage(),
        logger_factory=lambda name: (MagicMock(), lambda: None),
    )
    return executor, ctrl, pubsub_mock


def _published_events(pubsub_mock: MagicMock) -> list[dict]:
    """Extract all events published to the EVENTS_CHANNEL."""
    return [
        json.loads(call.args[1])
        for call in pubsub_mock.publish.call_args_list
        if call.args[0] == EVENTS_CHANNEL
    ]


def _event_types(pubsub_mock: MagicMock) -> list[str]:
    return [e["type"] for e in _published_events(pubsub_mock)]


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


class TestStart:
    def test_start_file_not_found_publishes_failed(self):
        executor, ctrl, pubsub_mock = make_executor()

        executor.start("nonexistent.gcode", task_id=1)

        types = _event_types(pubsub_mock)
        assert EVENT_FILE_FAILED in types
        assert EVENT_FILE_STARTED not in types
        assert not executor.is_running

    def test_start_publishes_started_event(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\nG1 Y20\n")
        executor, ctrl, pubsub_mock = make_executor()

        executor.start(str(gcode), task_id=5)

        types = _event_types(pubsub_mock)
        assert EVENT_FILE_STARTED in types
        ev = next(e for e in _published_events(pubsub_mock) if e["type"] == EVENT_FILE_STARTED)
        assert ev["task_id"] == 5
        assert ev["total_lines"] == 2
        assert executor.is_running

    def test_start_registers_hooks(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()

        executor.start(str(gcode), task_id=1)

        assert ctrl._ok_hook is not None

    def test_start_twice_is_idempotent(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()

        executor.start(str(gcode), task_id=1)
        executor.start(str(gcode), task_id=2)  # ignored

        # Only one FILE_STARTED event
        assert _event_types(pubsub_mock).count(EVENT_FILE_STARTED) == 1


# ---------------------------------------------------------------------------
# tick() — normal line send
# ---------------------------------------------------------------------------


class TestTickNormal:
    def test_tick_sends_gcode_line(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0  # bypass rate limiter

        executor.tick()

        ctrl.send_command_mock.assert_called_once_with("G0 X10\n")
        assert executor._sent_lines == 1

    def test_tick_skipped_when_paused(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor.pause()
        executor._last_send = 0.0

        executor.tick()

        ctrl.send_command_mock.assert_not_called()

    def test_tick_skipped_when_buffer_full(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        ctrl = FakeController(buffer_fill=100.0)
        executor, ctrl, pubsub_mock = make_executor(controller=ctrl)
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()

        ctrl.send_command_mock.assert_not_called()

    def test_tick_rate_limited(self, tmp_path: Path):
        """Second tick within SEND_INTERVAL must not send another line."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\nG1 Y20\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends line 1
        # Don't reset _last_send — rate-limiter should block line 2
        executor.tick()

        assert ctrl.send_command_mock.call_count == 1


# ---------------------------------------------------------------------------
# tick() — processed_lines via on_ok hook
# ---------------------------------------------------------------------------


class TestProcessedLines:
    def test_ok_hook_increments_processed_lines(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)

        assert executor._processed_lines == 0
        executor._pending_file_cmds.append("G0 X10")
        ctrl.fire_ok("G0 X10")
        assert executor._processed_lines == 1

    def test_ok_hook_ignored_when_not_running(self, tmp_path: Path):
        executor, ctrl, pubsub_mock = make_executor()
        # Not started; manually set a stale hook by calling _on_ok directly
        executor._on_ok("G0 X10")
        assert executor._processed_lines == 0

    def test_get_progress_uses_processed_lines(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=7)

        executor._pending_file_cmds.append("G0 X10")
        ctrl.fire_ok("G0 X10")

        progress = executor.get_progress()
        assert progress["processed_lines"] == 1
        assert progress["task_id"] == 7


# ---------------------------------------------------------------------------
# tick() — empty / comment lines
# ---------------------------------------------------------------------------


class TestEmptyCommentLines:
    @pytest.mark.parametrize("line", ["", "  ", "; this is a comment", "(a comment)"])
    def test_empty_or_comment_increments_processed_without_send(self, tmp_path: Path, line: str):
        gcode = tmp_path / "test.gcode"
        gcode.write_text(line + "\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()

        ctrl.send_command_mock.assert_not_called()
        assert executor._processed_lines == 1
        assert executor._sent_lines == 1


# ---------------------------------------------------------------------------
# tick() — program end detection (M2/M30)
# ---------------------------------------------------------------------------


class TestProgramEndDetection:
    @pytest.mark.parametrize("end_cmd", ["M2", "M02", "M30", "m30", "m2"])
    def test_tick_detects_program_end_publishes_finished(self, tmp_path: Path, end_cmd: str):
        gcode = tmp_path / "test.gcode"
        gcode.write_text(f"G0 X10\n{end_cmd}\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=3)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        executor._last_send = 0.0
        executor.tick()  # sends program-end → enters draining mode

        assert executor._draining is True
        assert executor.is_running

        ctrl.fire_ok("G0 X10")  # ack first command
        ctrl.fire_ok(end_cmd)  # ack program-end → queue empty
        pubsub_mock.reset_mock()
        executor.tick()  # draining + empty → publish FINISHED

        types = _event_types(pubsub_mock)
        assert EVENT_FILE_FINISHED in types
        assert not executor.is_running

    def test_tick_program_end_deregisters_hooks(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("M30\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends M30 → enters draining
        ctrl.fire_ok("M30")  # ack → queue empty
        executor.tick()  # draining + empty → reset → hook cleared

        assert ctrl._ok_hook is None

    def test_tick_program_end_file_is_closed(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("M30\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # _close_file() is called immediately on program-end

        assert executor._gcode is None


# ---------------------------------------------------------------------------
# tick() — EOF without program end
# ---------------------------------------------------------------------------


class TestEof:
    def test_eof_publishes_finished(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X5\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=2)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X5
        executor._last_send = 0.0
        executor.tick()  # EOF → enters draining mode

        assert executor._draining is True
        assert executor.is_running  # still running while draining

        ctrl.fire_ok("G0 X5")  # ack → queue empty
        pubsub_mock.reset_mock()
        executor.tick()  # draining + empty → publish FINISHED

        types = _event_types(pubsub_mock)
        assert EVENT_FILE_FINISHED in types
        assert not executor.is_running

    def test_eof_deregisters_hooks(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X5\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X5
        executor._last_send = 0.0
        executor.tick()  # EOF → draining

        ctrl.fire_ok("G0 X5")  # ack
        executor.tick()  # draining + empty → reset → hook cleared

        assert ctrl._ok_hook is None


# ---------------------------------------------------------------------------
# tick() — CNC error
# ---------------------------------------------------------------------------


class TestCncError:
    def test_tick_grbl_error_publishes_failed(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        ctrl = FakeController()
        ctrl._failed = True
        ctrl._error_message = "Error:25"
        executor, ctrl, pubsub_mock = make_executor(controller=ctrl)
        executor.start(str(gcode), task_id=4)
        executor._last_send = 0.0

        executor.tick()

        types = _event_types(pubsub_mock)
        # FILE_STARTED + FILE_FAILED
        assert EVENT_FILE_FAILED in types
        assert not executor.is_running

    def test_tick_grbl_error_deregisters_hooks(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        ctrl = FakeController()
        ctrl._failed = True
        ctrl._error_message = "Error:25"
        executor, ctrl, pubsub_mock = make_executor(controller=ctrl)
        executor.start(str(gcode), task_id=4)
        executor._last_send = 0.0

        executor.tick()

        assert ctrl._ok_hook is None


# ---------------------------------------------------------------------------
# _on_stall()
# ---------------------------------------------------------------------------


class TestOnStall:
    def test_stall_publishes_failed_with_stall_message(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=6)

        executor._on_stall()

        events = _published_events(pubsub_mock)
        failed_events = [e for e in events if e["type"] == EVENT_FILE_FAILED]
        assert len(failed_events) == 1
        assert "stall" in failed_events[0]["error"].lower()

    def test_stall_resets_state(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=6)

        executor._on_stall()

        assert not executor.is_running
        assert ctrl._ok_hook is None

    def test_stall_ignored_when_not_running(self):
        executor, ctrl, pubsub_mock = make_executor()

        executor._on_stall()  # should not raise or publish

        pubsub_mock.publish.assert_not_called()


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


class TestStop:
    def test_stop_publishes_failed_stopped_by_user(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=9)

        executor.stop()

        events = _published_events(pubsub_mock)
        failed = [e for e in events if e["type"] == EVENT_FILE_FAILED]
        assert len(failed) == 1
        assert failed[0]["error"] == "Stopped by user"

    def test_stop_deregisters_hooks(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=9)

        executor.stop()

        assert ctrl._ok_hook is None

    def test_stop_when_not_running_is_noop(self):
        executor, ctrl, pubsub_mock = make_executor()

        executor.stop()  # should not raise

        pubsub_mock.publish.assert_not_called()


# ---------------------------------------------------------------------------
# get_progress()
# ---------------------------------------------------------------------------


class TestGetProgress:
    def test_get_progress_returns_zero_processed_when_not_running(self):
        executor, ctrl, pubsub_mock = make_executor()

        progress = executor.get_progress()

        assert progress["processed_lines"] == 0

    def test_get_progress_when_running(self, tmp_path: Path):
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\nG1 Y20\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=11)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        ctrl.fire_ok("G0 X10")

        progress = executor.get_progress()
        assert progress["sent_lines"] == 1
        assert progress["processed_lines"] == 1
        assert progress["total_lines"] == 2
        assert progress["task_id"] == 11


# ---------------------------------------------------------------------------
# tick() — stall watchdog
# ---------------------------------------------------------------------------


class TestWatchdog:
    def test_tick_stall_triggers_failed_event(self, tmp_path: Path):
        """When pending file commands exist and STALL_TIMEOUT has elapsed,
        tick() must publish EVENT_FILE_FAILED and stop execution."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\nG1 Y20\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        # Simulate: one file command sent, no ok received, timeout elapsed
        executor._pending_file_cmds.append("G0 X10")
        executor._last_ok_time = 0.0  # stale — well past STALL_TIMEOUT
        executor._last_send = 0.0

        executor.tick()

        types = _event_types(pubsub_mock)
        assert EVENT_FILE_FAILED in types
        failed = next(e for e in _published_events(pubsub_mock) if e["type"] == EVENT_FILE_FAILED)
        assert "stall" in failed["error"].lower()
        assert not executor.is_running

    def test_tick_stall_deregisters_ok_hook(self, tmp_path: Path):
        """After a stall, the ok hook must be cleared."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        executor._pending_file_cmds.append("G0 X10")
        executor._last_ok_time = 0.0
        executor._last_send = 0.0

        executor.tick()

        assert ctrl._ok_hook is None

    def test_tick_no_stall_when_no_pending_commands(self, tmp_path: Path):
        """When the pending-file-cmds queue is empty, watchdog must not fire."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        # Queue is empty — all file commands acknowledged (or none sent yet)
        # _last_ok_time is stale, but without pending commands watchdog stays quiet
        executor._last_ok_time = 0.0
        executor._last_send = 0.0

        executor.tick()

        # Must NOT publish a failed event — should send the next line instead
        assert EVENT_FILE_FAILED not in _event_types(pubsub_mock)
        assert executor.is_running

    def test_tick_no_stall_when_timeout_not_elapsed(self, tmp_path: Path):
        """When timeout has NOT elapsed, watchdog must not fire."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        executor._pending_file_cmds.append("G0 X10")
        executor._last_ok_time = time.time()  # fresh
        executor._last_send = 0.0

        executor.tick()

        assert EVENT_FILE_FAILED not in _event_types(pubsub_mock)
        assert executor.is_running

    def test_ok_hook_resets_last_ok_time(self, tmp_path: Path):
        """Receiving an ok must update _last_ok_time, preventing stall false-positives."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        executor._pending_file_cmds.append("G0 X10")
        executor._last_ok_time = 0.0  # stale
        before = time.time()
        ctrl.fire_ok("G0 X10")

        assert executor._last_ok_time >= before

    def test_ok_ignored_when_not_file_command(self, tmp_path: Path):
        """An ok for an out-of-band command ($G, $J, etc.) must not increment
        _processed_lines or update _last_ok_time."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=12)

        # No file command enqueued — simulates an out-of-band $G ok
        old_ok_time = executor._last_ok_time
        ctrl.fire_ok("$G")

        assert executor._processed_lines == 0
        assert executor._last_ok_time == old_ok_time


# ---------------------------------------------------------------------------
# tick() — draining mode
# ---------------------------------------------------------------------------


class TestDrainingMode:
    def test_eof_enters_draining_not_finished(self, tmp_path: Path):
        """After the EOF tick, executor must be in draining mode (running but not sending);
        EVENT_FILE_FINISHED must NOT be published until the pending ok arrives."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        executor._last_send = 0.0
        executor.tick()  # EOF → draining

        assert executor._draining is True
        assert executor.is_running
        assert EVENT_FILE_FINISHED not in _event_types(pubsub_mock)

    def test_program_end_enters_draining_not_finished(self, tmp_path: Path):
        """After the M30 tick, executor is in draining mode; FINISHED only after ack."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("M30\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends M30 → draining

        assert executor._draining is True
        assert executor.is_running
        assert EVENT_FILE_FINISHED not in _event_types(pubsub_mock)

    def test_file_with_only_comments_finishes_on_eof_tick(self, tmp_path: Path):
        """A file containing only comments sends nothing to GRBL; the EOF tick
        must publish FINISHED immediately (no pending acks to wait for)."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("; comment\n; another\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # reads '; comment'
        executor._last_send = 0.0
        executor.tick()  # reads '; another'
        executor._last_send = 0.0
        executor.tick()  # EOF → no pending cmds → FINISHED immediately

        assert EVENT_FILE_FINISHED in _event_types(pubsub_mock)
        assert not executor.is_running

    def test_draining_not_blocked_by_pause(self, tmp_path: Path):
        """Pausing must not prevent tick() from completing the drain once all
        acks have arrived."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        executor._last_send = 0.0
        executor.tick()  # EOF → draining
        executor.pause()  # paused while draining

        ctrl.fire_ok("G0 X10")  # ack arrives from I/O thread
        pubsub_mock.reset_mock()
        executor.tick()  # paused but draining → drain block fires before pause guard

        assert EVENT_FILE_FINISHED in _event_types(pubsub_mock)
        assert not executor.is_running

    def test_stall_fires_during_draining(self, tmp_path: Path):
        """If GRBL stops sending acks while in draining mode, the stall watchdog
        must still trigger EVENT_FILE_FAILED."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock = make_executor()
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        executor._last_send = 0.0
        executor.tick()  # EOF → draining

        # Simulate stall: ack never arrives and timeout has elapsed
        executor._last_ok_time = 0.0
        executor.tick()

        assert EVENT_FILE_FAILED in _event_types(pubsub_mock)
        assert not executor.is_running

    def test_grbl_error_during_draining_publishes_failed(self, tmp_path: Path):
        """A GRBL error that arrives while draining must publish EVENT_FILE_FAILED."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        ctrl = FakeController()
        executor, ctrl, pubsub_mock = make_executor(controller=ctrl)
        executor.start(str(gcode), task_id=1)
        executor._last_send = 0.0

        executor.tick()  # sends G0 X10
        executor._last_send = 0.0
        executor.tick()  # EOF → draining

        # Inject error while in draining mode
        ctrl._failed = True
        ctrl._error_message = "Error:2"
        executor.tick()

        assert EVENT_FILE_FAILED in _event_types(pubsub_mock)
        assert not executor.is_running


# ---------------------------------------------------------------------------
# Shared logger cleanup
# ---------------------------------------------------------------------------


class TestSharedLoggerCleanup:
    """Verify that the task FileHandler is always removed when execution ends."""

    def _make_executor_with_spy_factory(
        self,
    ) -> tuple[FileExecutor, FakeController, MagicMock, list[MagicMock]]:
        """Return an executor whose logger_factory records every cleanup callable."""
        ctrl = FakeController()
        pubsub_mock = MagicMock()
        cleanups: list[MagicMock] = []

        def spy_factory(name: str | None):
            cleanup = MagicMock()
            cleanups.append(cleanup)
            return MagicMock(), cleanup

        executor = FileExecutor(
            ctrl,
            pubsub_client=pubsub_mock,
            storage=FakeFileStorage(),
            logger_factory=spy_factory,
        )
        return executor, ctrl, pubsub_mock, cleanups

    def _get_cleanup_for_start(self, cleanups: list[MagicMock]) -> MagicMock:
        """Returns the cleanup registered during execution start.

        It requires discarding the first two elements, since they correspond to the calls
        of logger_factory in the constructor.
        """

        return cleanups[2]

    def test_cleanup_called_on_successful_finish(self, tmp_path: Path) -> None:
        """cleanup() must be called after a file finishes successfully."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, pubsub_mock, cleanups = self._make_executor_with_spy_factory()

        executor.start(str(gcode), task_id=1, shared_logger_name="task_test_123")
        task_cleanup = self._get_cleanup_for_start(cleanups)

        executor._last_send = 0.0
        executor.tick()  # sends G0 X10
        ctrl.fire_ok("G0 X10")
        executor._last_send = 0.0
        executor.tick()  # EOF → draining
        executor.tick()  # drain resolves → FINISHED + _reset_state

        task_cleanup.assert_called_once()

    def test_cleanup_called_on_stop(self, tmp_path: Path) -> None:
        """cleanup() must be called when the user stops execution."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, _, cleanups = self._make_executor_with_spy_factory()

        executor.start(str(gcode), task_id=2, shared_logger_name="task_test_456")
        task_cleanup = self._get_cleanup_for_start(cleanups)

        executor.stop()

        task_cleanup.assert_called_once()

    def test_cleanup_called_on_grbl_error(self, tmp_path: Path) -> None:
        """cleanup() must be called when GRBL reports an error during execution."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        ctrl = FakeController()
        executor, ctrl, _, cleanups = self._make_executor_with_spy_factory()
        # Override controller with an error-prone one
        executor.controller = ctrl

        executor.start(str(gcode), task_id=3, shared_logger_name="task_test_789")
        task_cleanup = self._get_cleanup_for_start(cleanups)

        ctrl._failed = True
        ctrl._error_message = "Error:2"
        executor._last_send = 0.0
        executor.tick()

        task_cleanup.assert_called_once()

    def test_cleanup_called_on_stall(self, tmp_path: Path) -> None:
        """cleanup() must be called when the stall watchdog fires."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, _, cleanups = self._make_executor_with_spy_factory()

        executor.start(str(gcode), task_id=4, shared_logger_name="task_test_stall")
        task_cleanup = self._get_cleanup_for_start(cleanups)

        executor._last_send = 0.0
        executor.tick()  # sends G0 X10 — pending ack
        executor._last_ok_time = 0.0  # force stall timeout
        executor.tick()

        task_cleanup.assert_called_once()

    def test_cleanup_called_on_file_not_found(self) -> None:
        """cleanup() must be called even when the file does not exist."""
        executor, _, _, cleanups = self._make_executor_with_spy_factory()

        executor.start("nonexistent.gcode", task_id=5, shared_logger_name="task_test_missing")
        task_cleanup = self._get_cleanup_for_start(cleanups)

        task_cleanup.assert_called_once()

    def test_no_shared_logger_cleanup(self, tmp_path: Path) -> None:
        """When shared_logger_name is None the factory cleanup is also called."""
        gcode = tmp_path / "test.gcode"
        gcode.write_text("G0 X10\n")
        executor, ctrl, _, cleanups = self._make_executor_with_spy_factory()

        executor.start(str(gcode), task_id=6)  # no shared_logger_name
        task_cleanup = self._get_cleanup_for_start(cleanups)

        executor._last_send = 0.0
        executor.tick()
        ctrl.fire_ok("G0 X10")
        executor._last_send = 0.0
        executor.tick()  # EOF → draining
        executor.tick()  # FINISHED

        # The no-shared-logger cleanup is called
        task_cleanup.assert_called_once()

    def test_handler_not_accumulated_across_multiple_tasks(self, tmp_path: Path) -> None:
        """Each new task must trigger exactly one cleanup for the previous task,
        preventing unbounded handler accumulation."""
        handlers: list[MagicMock] = []
        handler_count_after: list[int] = []

        def tracking_factory(name: str | None):
            if name:
                handlers.append(MagicMock())

                def cleanup():
                    handlers.pop()

                return MagicMock(), cleanup
            return MagicMock(), lambda: None

        executor = FileExecutor(
            FakeController(),
            pubsub_client=MagicMock(),
            storage=FakeFileStorage(),
            logger_factory=tracking_factory,
        )

        for i in range(3):
            gcode = tmp_path / f"task{i}.gcode"
            gcode.write_text("G0 X1\n")
            executor.start(str(gcode), task_id=i, shared_logger_name=f"task_acc_{i}")
            executor._last_send = 0.0
            executor.tick()
            executor.controller.fire_ok("G0 X1")
            executor._last_send = 0.0
            executor.tick()  # EOF → draining
            executor.tick()  # FINISHED → _reset_state → cleanup
            handler_count_after.append(len(handlers))

        # After each task the handler added for that task must be gone
        assert all(count == 0 for count in handler_count_after), handler_count_after
