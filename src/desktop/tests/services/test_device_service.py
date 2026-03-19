import pytest
from desktop.services.deviceService import DeviceService
from pytest_mock.plugin import MockerFixture


class TestDeviceService:
    """Tests for DeviceService combined-check methods."""

    # --- is_device_available ---

    @pytest.mark.parametrize(
        "worker_connected,gateway_running,active_session,worker_busy,expected",
        [
            (True, True, False, False, True),
            (False, True, False, False, False),
            (True, False, False, False, False),
            (True, True, True, False, False),
            (True, True, False, True, False),
            (False, False, True, True, False),
        ],
    )
    def test_is_device_available(
        self,
        mocker: MockerFixture,
        worker_connected,
        gateway_running,
        active_session,
        worker_busy,
        expected,
    ):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=worker_connected)
        mocker.patch.object(DeviceService, "is_gateway_running", return_value=gateway_running)
        mocker.patch.object(DeviceService, "has_active_session", return_value=active_session)
        mocker.patch.object(DeviceService, "is_worker_busy", return_value=worker_busy)

        assert DeviceService.is_device_available() is expected

    # --- check_device_availability ---

    def test_check_device_availability_all_ok(self, mocker: MockerFixture):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=True)
        mocker.patch.object(DeviceService, "is_gateway_running", return_value=True)
        mocker.patch.object(DeviceService, "has_active_session", return_value=False)
        mocker.patch.object(DeviceService, "is_worker_busy", return_value=False)

        assert DeviceService.check_device_availability() is None

    def test_check_device_availability_worker_disconnected(self, mocker: MockerFixture):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=False)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "worker" in result.lower()

    def test_check_device_availability_gateway_not_running(self, mocker: MockerFixture):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=True)
        mocker.patch.object(DeviceService, "is_gateway_running", return_value=False)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "gateway" in result.lower()

    def test_check_device_availability_session_active(self, mocker: MockerFixture):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=True)
        mocker.patch.object(DeviceService, "is_gateway_running", return_value=True)
        mocker.patch.object(DeviceService, "has_active_session", return_value=True)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "sesión" in result.lower()

    def test_check_device_availability_worker_busy(self, mocker: MockerFixture):
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=True)
        mocker.patch.object(DeviceService, "is_gateway_running", return_value=True)
        mocker.patch.object(DeviceService, "has_active_session", return_value=False)
        mocker.patch.object(DeviceService, "is_worker_busy", return_value=True)

        result = DeviceService.check_device_availability()
        assert result is not None
        assert "progreso" in result.lower()
