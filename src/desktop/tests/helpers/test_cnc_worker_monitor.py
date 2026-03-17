import json
from unittest.mock import MagicMock

import pytest
from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENTS_CHANNEL,
    STATUS_CHANNEL,
)
from desktop.helpers.cncWorkerMonitor import CncWorkerMonitor
from desktop.services.deviceService import DeviceService
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _status_message(file_progress: dict | None = None, status=None, parserstate=None) -> dict:
    """Build a fake ``grbl_status`` PubSub raw message."""
    payload = {
        "status": status or {},
        "parserstate": parserstate or {},
        "gateway_state": "file_execution" if file_progress else "idle",
        "session": None,
        "file_progress": file_progress,
    }
    return {
        "type": "message",
        "channel": STATUS_CHANNEL.encode(),
        "data": json.dumps(payload),
    }


def _event_message(event_type: str, **kwargs) -> dict:
    """Build a fake ``cnc:events`` PubSub raw message."""
    payload = {"type": event_type, **kwargs}
    return {
        "type": "message",
        "channel": EVENTS_CHANNEL.encode(),
        "data": json.dumps(payload),
    }


def _subscribe_message() -> dict:
    """Subscription confirmation message (not a real message)."""
    return {"type": "subscribe", "channel": b"grbl_status", "data": 1}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCncWorkerMonitor:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        # Prevent real Redis connections
        self.mock_pubsub = MagicMock()
        mocker.patch(
            "desktop.helpers.cncWorkerMonitor.GatewayClient",
            return_value=MagicMock(subscribe_channels=MagicMock(return_value=self.mock_pubsub)),
        )
        self.monitor = CncWorkerMonitor()

    def test_start_and_stop_monitor(self):
        """start_task_monitor creates a daemon thread, stop sets _running=False."""
        self.mock_pubsub.get_message.return_value = None

        self.monitor.start_task_monitor()
        assert self.monitor._running is True
        assert self.monitor._thread is not None
        assert self.monitor._thread.daemon is True

        self.monitor.stop_task_monitor()
        assert self.monitor._running is False

    def test_status_progress_emits_signal(self, qtbot: QtBot, mocker: MockerFixture):
        """A grbl_status message with file_progress emits task_new_status."""
        status_data = {"activeState": "Run"}
        parser_data = {"feedrate": 500, "spindle": 1000, "tool": 1}

        status_msg = _status_message(
            file_progress={"sent_lines": 15, "processed_lines": 10, "total_lines": 20},
            status=status_data,
            parserstate=parser_data,
        )

        # Directly invoke _handle_status (unit-test the handler)
        def validate_signal(sent, processed, total, status, parserstate):
            return sent == 15 and processed == 10 and total == 20

        with qtbot.waitSignal(
            self.monitor.task_new_status,
            check_params_cb=validate_signal,
            raising=True,
        ):
            data = json.loads(status_msg["data"])
            self.monitor._handle_status(data)

    def test_status_without_progress_does_not_emit(self, qtbot: QtBot):
        """A grbl_status message without file_progress does NOT emit."""
        with qtbot.waitSignals(
            [self.monitor.task_new_status],
            raising=False,
            timeout=200,
        ) as blocker:
            self.monitor._handle_status({"status": {}, "parserstate": {}, "file_progress": None})

        assert blocker.signal_triggered is False

    def test_event_finished_emits_signal(self, qtbot: QtBot, mocker: MockerFixture):
        """A file_finished event emits task_finished and disables device."""
        mock_disable = mocker.patch.object(DeviceService, "set_device_enabled")

        event = {"type": EVENT_FILE_FINISHED, "sent_lines": 20, "total_lines": 20}

        with qtbot.waitSignal(self.monitor.task_finished, raising=True):
            self.monitor._handle_event(event)

        assert self.monitor._running is False
        mock_disable.assert_called_once_with(False)

    def test_event_failed_emits_signal(self, qtbot: QtBot, mocker: MockerFixture):
        """A file_failed event emits task_failed with error message."""
        mock_disable = mocker.patch.object(DeviceService, "set_device_enabled")

        event = {"type": EVENT_FILE_FAILED, "error": "GRBL alarm"}

        def validate_failed(msg: str):
            return msg == "GRBL alarm"

        with qtbot.waitSignal(
            self.monitor.task_failed,
            check_params_cb=validate_failed,
            raising=True,
        ):
            self.monitor._handle_event(event)

        assert self.monitor._running is False
        mock_disable.assert_called_once_with(False)

    def test_event_failed_default_error(self, qtbot: QtBot, mocker: MockerFixture):
        """A file_failed event without 'error' key uses default message."""
        mocker.patch.object(DeviceService, "set_device_enabled")

        event = {"type": EVENT_FILE_FAILED}

        def validate_failed(msg: str):
            return msg == "Error desconocido"

        with qtbot.waitSignal(
            self.monitor.task_failed,
            check_params_cb=validate_failed,
            raising=True,
        ):
            self.monitor._handle_event(event)

    def test_listen_dispatches_channels(self, mocker: MockerFixture):
        """The _listen loop correctly dispatches by channel name."""
        handle_status = mocker.patch.object(self.monitor, "_handle_status")
        handle_event = mocker.patch.object(self.monitor, "_handle_event")

        status_msg = _status_message(
            file_progress={"sent_lines": 1, "processed_lines": 0, "total_lines": 10}
        )
        event_msg = _event_message(EVENT_FILE_FINISHED, sent_lines=10, total_lines=10)

        call_count = 0

        def fake_get_message(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _subscribe_message()
            if call_count == 2:
                return status_msg
            if call_count == 3:
                # Stop the monitor after delivering the event
                self.monitor._running = False
                return event_msg
            return None

        self.mock_pubsub.get_message.side_effect = fake_get_message
        self.monitor._running = True
        self.monitor._listen()

        assert handle_status.call_count == 1
        assert handle_event.call_count == 1
