"""Tests for :class:`GatewaySync`."""

import json

import pytest
from core.utilities.gateway.constants import (
    EVENT_FILE_FAILED,
    EVENT_FILE_FINISHED,
    EVENTS_CHANNEL,
    STATUS_CHANNEL,
)
from desktop.helpers.gatewaySync import GatewaySync
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot

# ---------------------------------------------------------------------------
# Module-level patch: prevent real Redis connections
# ---------------------------------------------------------------------------

_MOCK_GW = "desktop.helpers.gatewaySync.GatewayClient"


@pytest.fixture(autouse=True)
def _patch_gateway(mocker: MockerFixture):
    mocker.patch(_MOCK_GW)


class TestGatewaySync:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.sync = GatewaySync()

    # -- start / stop -------------------------------------------------------

    def test_start_and_stop_monitor(self):
        self.sync.start_monitor()
        assert self.sync._running is True
        assert self.sync._thread is not None

        self.sync.stop_monitor()
        assert self.sync._running is False

    # -- _handle_status -----------------------------------------------------

    def test_status_emits_new_status(self, qtbot: QtBot):
        status = {"activeState": "Idle", "mpos": {}, "wpos": {}, "ov": [], "wco": {}}
        parserstate = {"modal": {}, "tool": 0, "feedrate": 0.0, "spindle": 0.0}
        data = {"status": status, "parserstate": parserstate, "file_progress": None}

        with qtbot.waitSignal(self.sync.new_status, raising=True):
            self.sync._handle_status(data)

    def test_status_with_file_progress_emits_signal(self, qtbot: QtBot):
        data = {
            "status": {"activeState": "Run", "mpos": {}, "wpos": {}, "ov": [], "wco": {}},
            "parserstate": {"modal": {}, "tool": 0, "feedrate": 0.0, "spindle": 0.0},
            "file_progress": {
                "sent_lines": 10,
                "processed_lines": 8,
                "total_lines": 100,
            },
        }

        with qtbot.waitSignal(self.sync.file_progress, raising=True):
            self.sync._handle_status(data)

    def test_status_without_progress_does_not_emit_file_progress(self, qtbot: QtBot):
        data = {
            "status": {"activeState": "Idle", "mpos": {}, "wpos": {}, "ov": [], "wco": {}},
            "parserstate": {"modal": {}, "tool": 0, "feedrate": 0.0, "spindle": 0.0},
            "file_progress": None,
        }

        with qtbot.waitSignal(self.sync.file_progress, timeout=200, raising=False) as blocker:
            self.sync._handle_status(data)

        assert blocker.signal_triggered is False

    # -- _handle_event ------------------------------------------------------

    def test_event_file_finished_emits_signal(self, qtbot: QtBot):
        data = {"type": EVENT_FILE_FINISHED, "task_id": 1}

        with qtbot.waitSignal(self.sync.file_finished, raising=True):
            self.sync._handle_event(data)

    def test_event_file_failed_emits_signal(self, qtbot: QtBot):
        data = {"type": EVENT_FILE_FAILED, "error": "E-Stop pressed"}

        with qtbot.waitSignal(self.sync.file_failed, raising=True):
            self.sync._handle_event(data)

    def test_event_file_failed_default_error(self, qtbot: QtBot):
        data = {"type": EVENT_FILE_FAILED}

        with qtbot.waitSignal(self.sync.file_failed, raising=True) as blocker:
            self.sync._handle_event(data)

        assert blocker.args == ["Error desconocido"]

    # -- _listen dispatches -------------------------------------------------

    def test_listen_dispatches_status_channel(self, mocker: MockerFixture):
        mock_handle_status = mocker.patch.object(GatewaySync, "_handle_status")
        payload = {"status": {}, "parserstate": {}}

        fake_msg = {
            "type": "message",
            "channel": STATUS_CHANNEL,
            "data": json.dumps(payload),
        }

        mock_pubsub = mocker.MagicMock()
        mocker.patch.object(self.sync._gateway, "subscribe_channels", return_value=mock_pubsub)

        self.sync._running = True
        call_count = 0

        def side_effect_fn(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fake_msg
            self.sync._running = False
            return None

        mock_pubsub.get_message.side_effect = side_effect_fn

        self.sync._listen()

        mock_handle_status.assert_called_once_with(payload)

    def test_listen_dispatches_events_channel(self, mocker: MockerFixture):
        mock_handle_event = mocker.patch.object(GatewaySync, "_handle_event")
        payload = {"type": EVENT_FILE_FINISHED}

        fake_msg = {
            "type": "message",
            "channel": EVENTS_CHANNEL,
            "data": json.dumps(payload),
        }

        mock_pubsub = mocker.MagicMock()
        mocker.patch.object(self.sync._gateway, "subscribe_channels", return_value=mock_pubsub)

        self.sync._running = True
        call_count = 0

        def side_effect_fn(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fake_msg
            self.sync._running = False
            return None

        mock_pubsub.get_message.side_effect = side_effect_fn

        self.sync._listen()

        mock_handle_event.assert_called_once_with(payload)
