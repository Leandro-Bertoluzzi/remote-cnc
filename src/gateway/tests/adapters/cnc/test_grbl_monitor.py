from unittest.mock import MagicMock

import pytest
from gateway.adapters.cnc.monitor import GrblMonitor
from gateway.adapters.cnc.parsers.grblMsgTypes import GRBL_MSG_STATUS
from mocks.logger import FakeLogger
from pytest_mock.plugin import MockerFixture


class TestGrblMonitor:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.grbl_logger = FakeLogger()

        # Inject a mock Pub/Sub client — no real connection attempted
        self.mock_pubsub = MagicMock()

        # Instantiate monitor
        self.grbl_monitor = GrblMonitor(self.grbl_logger, pubsub_client=self.mock_pubsub)

    @pytest.mark.parametrize("queue", [False, True])
    def test_debug(self, mocker: MockerFixture, queue):
        self.grbl_monitor.debug("Test message", queue)

        assert len(self.grbl_logger.debug_calls) == 1

    @pytest.mark.parametrize("queue", [False, True])
    def test_info(self, mocker: MockerFixture, queue):
        self.grbl_monitor.info("Test message", queue)

        assert len(self.grbl_logger.info_calls) == 1

    @pytest.mark.parametrize("queue", [False, True])
    def test_warning(self, mocker: MockerFixture, queue):
        self.grbl_monitor.warning("Test message", queue)

        assert len(self.grbl_logger.warning_calls) == 1

    @pytest.mark.parametrize("queue", [False, True])
    def test_error(self, mocker: MockerFixture, queue):
        self.grbl_monitor.error("Test message", queue)

        assert len(self.grbl_logger.error_calls) == 1

    @pytest.mark.parametrize("queue", [False, True])
    def test_critical(self, mocker: MockerFixture, queue):
        self.grbl_monitor.critical("Test message", exc_info=False, queue=queue)

        assert len(self.grbl_logger.critical_calls) == 1

    @pytest.mark.parametrize("debug", [False, True])
    def test_sent(self, mocker: MockerFixture, debug):
        self.grbl_monitor.sent("Test command", debug)

        assert len(self.grbl_logger.debug_calls) == (1 if debug else 0)
        assert len(self.grbl_logger.info_calls) == (0 if debug else 1)

    @pytest.mark.parametrize("msgType", [GRBL_MSG_STATUS, "AnotherType", None])
    def test_received(self, mocker: MockerFixture, msgType):
        debug = msgType == GRBL_MSG_STATUS
        self.grbl_monitor.received("Test message", msgType, {"key": "value"})

        assert len(self.grbl_logger.debug_calls) == (2 if debug else 0)
        assert len(self.grbl_logger.info_calls) == (0 if debug else 2)
