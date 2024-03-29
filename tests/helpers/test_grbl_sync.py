from core.grbl.grblController import GrblController
import core.mocks.grbl_mocks as grbl_mocks
from helpers.grblSync import GrblSync
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
            self.grbl_controller,
            'getStatusReport',
            return_value=grbl_mocks.grbl_status
        )
        mocker.patch.object(
            self.grbl_controller,
            'getFeedrate',
            return_value=50.0
        )
        mocker.patch.object(
            self.grbl_controller,
            'getSpindle',
            return_value=250.0
        )
        mocker.patch.object(
            self.grbl_controller,
            'getTool',
            return_value=1
        )

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.grbl_sync.new_status, raising=True):
            self.grbl_sync.get_status()
