import pytest
from core.utilities.worker.workerStatusManager import WorkerStoreAdapter
from desktop.services.deviceService import DeviceService
from pytest_mock.plugin import MockerFixture


class TestDeviceService:
    """Tests for DeviceService combined-check methods."""

    # --- is_device_available ---

    @pytest.mark.parametrize(
        "worker_connected,device_enabled,worker_busy,expected",
        [
            (True, True, False, True),
            (False, True, False, False),
            (True, False, False, False),
            (True, True, True, False),
            (False, False, True, False),
        ],
    )
    def test_is_device_available(
        self, mocker: MockerFixture, worker_connected, device_enabled, worker_busy, expected
    ):
        mocker.patch("core.utilities.worker.utils.is_worker_on", return_value=worker_connected)
        mocker.patch.object(WorkerStoreAdapter, "is_device_enabled", return_value=device_enabled)
        mocker.patch("core.utilities.worker.utils.is_worker_running", return_value=worker_busy)

        assert DeviceService.is_device_available() is expected

    # --- check_device_availability ---

    def test_check_device_availability_all_ok(self, mocker: MockerFixture):
        mocker.patch("core.utilities.worker.utils.is_worker_on", return_value=True)
        mocker.patch.object(WorkerStoreAdapter, "is_device_enabled", return_value=True)
        mocker.patch("core.utilities.worker.utils.is_worker_running", return_value=False)

        assert DeviceService.check_device_availability() is None

    def test_check_device_availability_worker_disconnected(self, mocker: MockerFixture):
        mocker.patch("core.utilities.worker.utils.is_worker_on", return_value=False)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "worker" in result.lower()

    def test_check_device_availability_device_disabled(self, mocker: MockerFixture):
        mocker.patch("core.utilities.worker.utils.is_worker_on", return_value=True)
        mocker.patch.object(WorkerStoreAdapter, "is_device_enabled", return_value=False)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "deshabilitado" in result.lower()

    def test_check_device_availability_worker_busy(self, mocker: MockerFixture):
        mocker.patch("core.utilities.worker.utils.is_worker_on", return_value=True)
        mocker.patch.object(WorkerStoreAdapter, "is_device_enabled", return_value=True)
        mocker.patch("core.utilities.worker.utils.is_worker_running", return_value=True)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "progreso" in result.lower()

    # --- Delegation methods ---

    def test_request_pause(self, mocker: MockerFixture):
        mock = mocker.patch.object(WorkerStoreAdapter, "request_pause")
        DeviceService.request_pause()
        mock.assert_called_once()

    def test_request_resume(self, mocker: MockerFixture):
        mock = mocker.patch.object(WorkerStoreAdapter, "request_resume")
        DeviceService.request_resume()
        mock.assert_called_once()

    def test_set_device_enabled(self, mocker: MockerFixture):
        mock = mocker.patch.object(WorkerStoreAdapter, "set_device_enabled")
        DeviceService.set_device_enabled(True)
        mock.assert_called_once_with(True)
