from utilities.grbl.grblController import GrblController
import mocks.grbl_mocks as grbl_mocks
from desktop.helpers.grblSync import GrblSync
from logging import Logger
from PyQt5.QtCore import QTimer
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestGrblSync:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Create an instance of GRBL synchronizer
        self.grbl_controller = GrblController(Logger('test-logger'))
        self.grbl_sync = GrblSync(self.grbl_controller)

    def test_grbl_sync_start_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_start = mocker.patch.object(QTimer, 'start')

        # Call method under test
        self.grbl_sync.start_monitor()

        # Assertions
        assert mock_timer_start.call_count == 2

    def test_grbl_sync_stop_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_stop = mocker.patch.object(QTimer, 'stop')

        # Call method under test
        self.grbl_sync.stop_monitor()

        # Assertions
        assert mock_timer_stop.call_count == 2

    def test_grbl_sync_message_received(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock GRBL monitor methods
        mocker.patch.object(
            self.grbl_controller.grbl_monitor,
            'getLog',
            return_value='A message'
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.grbl_sync.new_message, raising=True):
            self.grbl_sync.get_command()

    def test_grbl_sync_status_received(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock GRBL controller methods
        mocker.patch.object(
            self.grbl_controller.grbl_status,
            'get_status_report',
            return_value=grbl_mocks.grbl_status
        )
        mocker.patch.object(
            self.grbl_controller.grbl_status,
            'get_parser_state',
            return_value=grbl_mocks.grbl_parserstate
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.grbl_sync.new_status, raising=True):
            self.grbl_sync.get_status()

    def test_grbl_sync_grbl_failed(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock GRBL controller methods
        mocker.patch.object(
            self.grbl_controller.grbl_status,
            'failed',
            return_value=True
        )
        mocker.patch.object(
            self.grbl_controller.grbl_status,
            'get_error_message',
            return_value='An error message'
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.grbl_sync.failed, raising=True):
            self.grbl_sync.get_status()

        # Assertions
        self.grbl_sync._has_error is True

    def test_grbl_sync_grbl_recovers_from_failed(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock state
        self.grbl_sync._has_error = True

        # Mock GRBL controller methods
        mocker.patch.object(
            self.grbl_controller.grbl_status,
            'failed',
            return_value=False
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.grbl_sync.failed, timeout=500, raising=False) as blocker:
            self.grbl_sync.get_status()

        # Assertions
        self.grbl_sync._has_error is False
        # Check whether the signal was triggered
        assert blocker.signal_triggered is False
