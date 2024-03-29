from celery.result import AsyncResult
from celery.app.control import Inspect
import core.mocks.celery_mocks as celery_mocks
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
        mock_disable_device = mocker.patch.object(CncWorkerMonitor, 'set_device_enabled')

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
        mock_disable_device = mocker.patch.object(CncWorkerMonitor, 'set_device_enabled')

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

    @pytest.mark.parametrize("worker_on", [False, True])
    def test_cnc_worker_monitor_is_worker_on(self, mocker: MockerFixture, worker_on):
        # Mock worker status
        pong = (celery_mocks.celery_pong if worker_on else None)
        mocker.patch(
            'helpers.cncWorkerMonitor.app.control.ping',
            return_value=pong
        )

        # Assertions
        assert CncWorkerMonitor.is_worker_on() == worker_on

    def test_cnc_worker_monitor_is_worker_on_fails(self, mocker: MockerFixture):
        # Mock worker status
        mocker.patch(
            'helpers.cncWorkerMonitor.app.control.ping',
            side_effect=Exception('mocked-error')
        )

        # Assertions
        assert CncWorkerMonitor.is_worker_on() is False

    @pytest.mark.parametrize("worker_running", [False, True])
    def test_cnc_worker_monitor_is_worker_running(
        self,
        mocker: MockerFixture,
        worker_running
    ):
        # Mock list of tasks from worker
        active_tasks = (celery_mocks.celery_worker_active_tasks if worker_running else None)
        mocker.patch.object(
            Inspect,
            'active',
            return_value=active_tasks
        )

        # Assertions
        assert CncWorkerMonitor.is_worker_running() == worker_running

    def test_cnc_worker_monitor_is_worker_running_fails(self, mocker: MockerFixture):
        # Mock list of tasks from worker
        mocker.patch.object(
            Inspect,
            'active',
            side_effect=Exception('mocked-error')
        )

        # Assertions
        assert CncWorkerMonitor.is_worker_running() is False

    def test_cnc_worker_monitor_get_worker_status(self, mocker: MockerFixture):
        # Mock Celery methods
        mocker.patch.object(
            Inspect,
            'ping',
            return_value=celery_mocks.celery_worker_pong
        )
        mocker.patch.object(
            Inspect,
            'stats',
            return_value=celery_mocks.celery_worker_stats
        )
        mocker.patch.object(
            Inspect,
            'registered',
            return_value=celery_mocks.celery_worker_registered_tasks
        )
        mocker.patch.object(
            Inspect,
            'active',
            return_value=celery_mocks.celery_worker_active_tasks
        )

        # Call method under test
        result = CncWorkerMonitor.get_worker_status()

        # Assertions
        assert result == {
            'availability': celery_mocks.celery_worker_pong,
            'stats': celery_mocks.celery_worker_stats,
            'registered_tasks': celery_mocks.celery_worker_registered_tasks,
            'active_tasks': celery_mocks.celery_worker_active_tasks
        }

    def test_cnc_worker_monitor_set_device_enabled(self):
        CncWorkerMonitor.set_device_enabled(True)
        assert CncWorkerMonitor.is_device_enabled() is True

        CncWorkerMonitor.set_device_enabled(False)
        assert CncWorkerMonitor.is_device_enabled() is False
