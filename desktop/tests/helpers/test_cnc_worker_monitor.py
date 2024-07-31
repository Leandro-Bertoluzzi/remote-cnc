from celery.result import AsyncResult
from core.worker.workerStatusManager import WorkerStoreAdapter
import core.mocks.grbl_mocks as grbl_mocks
import core.mocks.worker_mocks as worker_mocks
from core.grbl.types import Status, ParserState
from helpers.cncWorkerMonitor import CncWorkerMonitor
from PyQt5.QtCore import QTimer
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestCncWorkerMonitor:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Create an instance of CNC worker monitor
        self.cnc_worker_monitor = CncWorkerMonitor()

    def test_cnc_worker_monitor_start_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_start = mocker.patch.object(QTimer, 'start')

        # Call method under test
        self.cnc_worker_monitor.start_task_monitor(task_id='abcd-1234')

        # Assertions
        assert self.cnc_worker_monitor.active_task == 'abcd-1234'
        assert mock_timer_start.call_count == 1

    def test_cnc_worker_monitor_stop_monitor(self, mocker: MockerFixture):
        # Mock timer method
        mock_timer_stop = mocker.patch.object(QTimer, 'stop')

        # Call method under test
        self.cnc_worker_monitor.stop_task_monitor()

        # Assertions
        assert mock_timer_stop.call_count == 1

    def test_cnc_worker_monitor_check_task_status_pending(
        self,
        qtbot: QtBot,
        mocker: MockerFixture
    ):
        # Mock Celery task metadata
        task_info = 'Mocked error message'
        task_metadata = {
            'status': 'PENDING',
            'result': task_info
        }

        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=task_metadata
        )

        # Call method under test
        with qtbot.waitSignals(
            [
                self.cnc_worker_monitor.task_new_status,
                self.cnc_worker_monitor.task_finished,
                self.cnc_worker_monitor.task_failed
            ],
            raising=False,
            timeout=500
        ) as blocker:
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_query_task.call_count == 1
        assert mock_query_task_info.call_count == 2
        # qtbot.TimeoutError is not raised, so I can manually
        # check whether the signal was triggered:
        assert blocker.signal_triggered is False

    def test_cnc_worker_monitor_check_task_status_progress(
        self,
        qtbot: QtBot,
        mocker: MockerFixture
    ):
        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=worker_mocks.task_metadata_in_progress
        )

        # Validate parameters in emitted signal
        def validate_new_status_signal(
            sent_lines: int,
            processed_lines: int,
            total_lines: int,
            controller_status: Status,
            grbl_parserstate: ParserState
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
            raising=True
        ):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_query_task.call_count == 1
        assert mock_query_task_info.call_count == 2

    def test_cnc_worker_monitor_check_task_status_failed(
        self,
        qtbot: QtBot,
        mocker: MockerFixture
    ):
        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=worker_mocks.task_metadata_failure
        )

        # Mock other methods from the class
        mock_disable_device = mocker.patch.object(WorkerStoreAdapter, 'set_device_enabled')

        # Validate parameters in emitted signal
        def validate_failed_signal(message: str):
            return message == 'Mocked error message'

        # Call method under test and wait for signal
        with qtbot.waitSignal(
            self.cnc_worker_monitor.task_failed,
            check_params_cb=validate_failed_signal,
            raising=True
        ):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_query_task.call_count == 1
        assert mock_query_task_info.call_count == 2
        assert mock_disable_device.call_count == 1

    def test_cnc_worker_monitor_check_task_status_finished(
        self,
        qtbot: QtBot,
        mocker: MockerFixture
    ):
        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=worker_mocks.task_metadata_success
        )

        # Mock other methods from the class
        mock_disable_device = mocker.patch.object(WorkerStoreAdapter, 'set_device_enabled')

        # Call method under test and wait for signal
        with qtbot.waitSignal(
            self.cnc_worker_monitor.task_finished,
            raising=True
        ):
            self.cnc_worker_monitor.check_task_status()

        # Assertions
        assert mock_query_task.call_count == 1
        assert mock_query_task_info.call_count == 2
        assert mock_disable_device.call_count == 1
