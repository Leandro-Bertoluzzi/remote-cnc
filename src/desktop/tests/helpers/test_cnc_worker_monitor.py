import mocks.grbl as grbl_mocks
import pytest
from core.utilities.grbl.types import ParserState, Status
from desktop.helpers.cncWorkerMonitor import CncWorkerMonitor
from desktop.services.deviceService import DeviceService
from PyQt5.QtCore import QTimer
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestCncWorkerMonitor:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Create an instance of CNC worker monitor
        self.cnc_worker_monitor = CncWorkerMonitor()

    def test_cnc_worker_monitor_start_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_start = mocker.patch.object(QTimer, "start")

        # Call method under test
        self.cnc_worker_monitor.start_task_monitor(task_id="abcd-1234")

        # Assertions
        assert self.cnc_worker_monitor.active_task == "abcd-1234"
        assert mock_timer_start.call_count == 1

    def test_cnc_worker_monitor_stop_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_stop = mocker.patch.object(QTimer, "stop")

        # Call method under test
        self.cnc_worker_monitor.stop_task_monitor()

        # Assertions
        assert mock_timer_stop.call_count == 1

    def test_cnc_worker_monitor_check_task_status_pending(
        self, qtbot: QtBot, mocker: MockerFixture
    ):
        # Mock DeviceService to return PENDING status
        mock_get_status = mocker.patch.object(
            DeviceService,
            "get_celery_task_status",
            return_value={"status": "PENDING", "info": "Mocked error message"},
        )

        # Call method under test
        with qtbot.waitSignals(
            [
                self.cnc_worker_monitor.task_new_status,
                self.cnc_worker_monitor.task_finished,
                self.cnc_worker_monitor.task_failed,
            ],
            raising=False,
            timeout=500,
        ) as blocker:
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_get_status.call_count == 1
        # qtbot.TimeoutError is not raised, so I can manually
        # check whether the signal was triggered:
        assert blocker.signal_triggered is False

    def test_cnc_worker_monitor_check_task_status_progress(
        self, qtbot: QtBot, mocker: MockerFixture
    ):
        # Mock DeviceService to return PROGRESS status
        progress_info = {
            "sent_lines": 15,
            "processed_lines": 10,
            "total_lines": 20,
            "status": grbl_mocks.grbl_status,
            "parserstate": grbl_mocks.grbl_parserstate,
        }
        mock_get_status = mocker.patch.object(
            DeviceService,
            "get_celery_task_status",
            return_value={"status": "PROGRESS", "info": progress_info},
        )

        # Validate parameters in emitted signal
        def validate_new_status_signal(
            sent_lines: int,
            processed_lines: int,
            total_lines: int,
            controller_status: Status,
            grbl_parserstate: ParserState,
        ):
            return (
                sent_lines == 15
                and processed_lines == 10
                and total_lines == 20
                and controller_status == grbl_mocks.grbl_status
                and grbl_parserstate == grbl_mocks.grbl_parserstate
            )

        # Call method under test and wait for signal
        with qtbot.waitSignal(
            self.cnc_worker_monitor.task_new_status,
            check_params_cb=validate_new_status_signal,
            raising=True,
        ):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_get_status.call_count == 1

    def test_cnc_worker_monitor_check_task_status_failed(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock DeviceService to return FAILURE status
        mock_get_status = mocker.patch.object(
            DeviceService,
            "get_celery_task_status",
            return_value={"status": "FAILURE", "info": "Mocked error message"},
        )

        # Mock device disable call
        mock_disable_device = mocker.patch.object(DeviceService, "set_device_enabled")

        # Validate parameters in emitted signal
        def validate_failed_signal(message: str):
            return message == "Mocked error message"

        # Call method under test and wait for signal
        with qtbot.waitSignal(
            self.cnc_worker_monitor.task_failed,
            check_params_cb=validate_failed_signal,
            raising=True,
        ):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_get_status.call_count == 1
        assert mock_disable_device.call_count == 1

    def test_cnc_worker_monitor_check_task_status_finished(
        self, qtbot: QtBot, mocker: MockerFixture
    ):
        # Mock DeviceService to return SUCCESS status
        mock_get_status = mocker.patch.object(
            DeviceService,
            "get_celery_task_status",
            return_value={"status": "SUCCESS", "info": {}},
        )

        # Mock device disable call
        mock_disable_device = mocker.patch.object(DeviceService, "set_device_enabled")

        # Call method under test and wait for signal
        with qtbot.waitSignal(self.cnc_worker_monitor.task_finished, raising=True):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_get_status.call_count == 1
        assert mock_disable_device.call_count == 1
