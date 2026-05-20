"""Tests for gateway.CommandProcessor."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from core.domain.gateway import (
    ACTION_PAUSE,
    ACTION_RESUME,
    ACTION_SOFT_RESET,
    ACTION_STOP,
    MSG_COMMAND,
    MSG_DISCONNECT,
    MSG_FILE_START,
    MSG_FILE_STOP,
    MSG_JOG,
    MSG_QUERY,
    MSG_REALTIME,
)
from fakes import FakeController, FakeFileExecutor, FakeSessionManager
from gateway.commandProcessor import CommandProcessor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_processor(
    *,
    session_valid: bool = True,
    active_session: dict | None = None,
    file_running: bool = False,
) -> tuple[CommandProcessor, FakeController, FakeFileExecutor, FakeSessionManager, MagicMock]:
    controller = FakeController()
    session_manager = FakeSessionManager(
        active_session=active_session or {"session_id": "test-session"},
        session_valid=session_valid,
    )
    file_executor = FakeFileExecutor(running=file_running)
    redis_mock = MagicMock()
    processor = CommandProcessor(
        controller,
        session_manager,
        file_executor,
        redis_conn=redis_mock,
    )
    return processor, controller, file_executor, session_manager, redis_mock


def _blpop_result(
    msg_type: str, payload: dict, session_id: str = "test-session"
) -> tuple[bytes, bytes]:
    """Build a (queue_bytes, raw_json) tuple for redis_mock.blpop.return_value."""
    message = json.dumps({"type": msg_type, "session_id": session_id, "payload": payload})
    return (b"queue:high", message.encode())


def _queue(
    redis_mock: MagicMock,
    value: tuple[bytes, bytes] | None,
) -> None:
    """Set the next blpop result on *redis_mock*."""
    redis_mock.blpop.return_value = value


# ---------------------------------------------------------------------------
# process_one
# ---------------------------------------------------------------------------


class TestProcessOne:
    def test_returns_false_on_timeout(self):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, None)
        assert processor.process_one() is False

    def test_returns_true_when_message_processed(self):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_FILE_STOP, {}))
        assert processor.process_one() is True

    def test_returns_true_on_malformed_json(self):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, (b"queue:high", b"not-json"))
        assert processor.process_one() is True

    def test_malformed_json_does_not_dispatch(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, (b"queue:high", b"not-json"))
        processor.process_one()
        controller.send_command_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Session validation
# ---------------------------------------------------------------------------


class TestDispatchSessionValidation:
    def test_rejects_message_with_invalid_session(self):
        processor, controller, *_, redis_mock = make_processor(session_valid=False)
        _queue(redis_mock, _blpop_result(MSG_COMMAND, {"command": "G0 X10"}, session_id="bad"))
        processor.process_one()
        controller.send_command_mock.assert_not_called()

    def test_query_bypasses_session_validation(self):
        processor, controller, *_, redis_mock = make_processor(session_valid=False)
        _queue(redis_mock, _blpop_result(MSG_QUERY, {"query": "status"}, session_id="bad"))
        processor.process_one()
        controller.query_status_report_mock.assert_called_once()


# ---------------------------------------------------------------------------
# _handle_realtime
# ---------------------------------------------------------------------------


class TestHandleRealtime:
    @pytest.mark.parametrize(
        "action", [ACTION_PAUSE, ACTION_RESUME, ACTION_STOP, ACTION_SOFT_RESET]
    )
    def test_valid_action_does_not_log_warning(self, action, caplog):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": action}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid realtime payload" not in caplog.text

    def test_pause_calls_set_paused_true(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_PAUSE}))
        processor.process_one()
        controller.set_paused_mock.assert_called_once_with(True)

    def test_pause_calls_file_executor_pause_when_running(self):
        processor, _, file_executor, _, redis_mock = make_processor(file_running=True)
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_PAUSE}))
        processor.process_one()
        file_executor.pause.assert_called_once()

    def test_pause_does_not_call_file_executor_pause_when_not_running(self):
        processor, _, file_executor, _, redis_mock = make_processor(file_running=False)
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_PAUSE}))
        processor.process_one()
        file_executor.pause.assert_not_called()

    def test_resume_calls_set_paused_false(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_RESUME}))
        processor.process_one()
        controller.set_paused_mock.assert_called_once_with(False)

    def test_resume_calls_file_executor_resume_when_running(self):
        processor, _, file_executor, _, redis_mock = make_processor(file_running=True)
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_RESUME}))
        processor.process_one()
        file_executor.resume.assert_called_once()

    def test_stop_calls_soft_reset_and_file_stop_when_running(self):
        processor, controller, file_executor, _, redis_mock = make_processor(file_running=True)
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_STOP}))
        processor.process_one()
        controller.request_soft_reset_mock.assert_called_once()
        file_executor.stop.assert_called_once()

    def test_soft_reset_calls_request_soft_reset(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": ACTION_SOFT_RESET}))
        processor.process_one()
        controller.request_soft_reset_mock.assert_called_once()

    def test_invalid_action_logs_warning(self, caplog):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_REALTIME, {"action": "unknown_action"}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid realtime payload" in caplog.text


# ---------------------------------------------------------------------------
# _handle_command
# ---------------------------------------------------------------------------


class TestHandleCommand:
    def test_valid_command_calls_send_command(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_COMMAND, {"command": "G0 X10"}))
        processor.process_one()
        controller.send_command_mock.assert_called_once_with("G0 X10")

    def test_empty_command_logs_warning(self, caplog):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_COMMAND, {"command": ""}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid command payload" in caplog.text
        controller.send_command_mock.assert_not_called()

    def test_missing_command_key_logs_warning(self, caplog):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_COMMAND, {}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        controller.send_command_mock.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_jog
# ---------------------------------------------------------------------------


class TestHandleJog:
    def test_valid_jog_calls_controller_with_correct_values(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(
            redis_mock, _blpop_result(MSG_JOG, {"x": 10.0, "y": 5.0, "z": 2.0, "feedrate": 500.0})
        )
        processor.process_one()
        controller.jog_mock.assert_called_once()
        args, _kwargs = controller.jog_mock.call_args
        assert args == (10.0, 5.0, 2.0, 500.0)

    def test_invalid_jog_logs_warning(self, caplog):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_JOG, {"x": "not-a-number"}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid jog payload" in caplog.text
        controller.jog_mock.assert_not_called()

    def test_empty_jog_uses_defaults(self):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_JOG, {}))
        processor.process_one()
        controller.jog_mock.assert_called_once()
        args, _ = controller.jog_mock.call_args
        assert args == (0.0, 0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# _handle_file_start
# ---------------------------------------------------------------------------


class TestHandleFileStart:
    def test_valid_payload_calls_file_executor_start(self):
        processor, _, file_executor, _, redis_mock = make_processor()
        _queue(
            redis_mock,
            _blpop_result(MSG_FILE_START, {"file_path": "/tmp/test.gcode", "task_id": 1}),
        )
        processor.process_one()
        file_executor.start.assert_called_once_with("/tmp/test.gcode", 1)

    def test_missing_file_path_logs_warning(self, caplog):
        processor, _, file_executor, _, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_FILE_START, {"task_id": 1}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid file_start payload" in caplog.text
        file_executor.start.assert_not_called()

    def test_empty_file_path_logs_warning(self, caplog):
        processor, _, file_executor, _, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_FILE_START, {"file_path": "", "task_id": 1}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        file_executor.start.assert_not_called()

    def test_task_id_is_optional(self):
        processor, _, file_executor, _, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_FILE_START, {"file_path": "/tmp/test.gcode"}))
        processor.process_one()
        file_executor.start.assert_called_once_with("/tmp/test.gcode", None)


# ---------------------------------------------------------------------------
# _handle_file_stop
# ---------------------------------------------------------------------------


class TestHandleFileStop:
    def test_stops_executor_when_running(self):
        processor, _, file_executor, _, redis_mock = make_processor(file_running=True)
        _queue(redis_mock, _blpop_result(MSG_FILE_STOP, {}))
        processor.process_one()
        file_executor.stop.assert_called_once()

    def test_does_not_stop_when_not_running(self):
        processor, _, file_executor, _, redis_mock = make_processor(file_running=False)
        _queue(redis_mock, _blpop_result(MSG_FILE_STOP, {}))
        processor.process_one()
        file_executor.stop.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_query
# ---------------------------------------------------------------------------


QUERY_METHOD_MAP = [
    ("status", "query_status_report_mock"),
    ("parserstate", "query_gcode_parser_state_mock"),
    ("settings", "query_grbl_settings_mock"),
    ("params", "query_grbl_params_mock"),
    ("build_info", "query_build_info_mock"),
    ("help", "query_grbl_help_mock"),
]


class TestHandleQuery:
    @pytest.mark.parametrize("query_type,method_name", QUERY_METHOD_MAP)
    def test_valid_query_calls_correct_controller_method(self, query_type, method_name):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_QUERY, {"query": query_type}))
        processor.process_one()
        getattr(controller, method_name).assert_called_once()

    @pytest.mark.parametrize("query_type,method_name", QUERY_METHOD_MAP)
    def test_only_one_query_method_is_called(self, query_type, method_name):
        processor, controller, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_QUERY, {"query": query_type}))
        processor.process_one()
        for _qt, mn in QUERY_METHOD_MAP:
            if mn != method_name:
                getattr(controller, mn).assert_not_called()

    def test_unknown_query_type_logs_warning(self, caplog):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_QUERY, {"query": "unknown"}))
        with caplog.at_level("WARNING"):
            processor.process_one()
        assert "Invalid query payload" in caplog.text


# ---------------------------------------------------------------------------
# _handle_disconnect
# ---------------------------------------------------------------------------


class TestHandleDisconnect:
    def test_sets_should_stop_true(self):
        processor, *_, redis_mock = make_processor()
        _queue(redis_mock, _blpop_result(MSG_DISCONNECT, {}))
        assert processor.should_stop is False
        processor.process_one()
        assert processor.should_stop is True
