from unittest.mock import MagicMock

import pytest
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient
from desktop.application.device_service import DeviceService


def _make_service(
    worker_on=True,
    worker_running=False,
    gateway_running=True,
    active_session=None,
) -> DeviceService:
    gateway = MagicMock(spec=IGatewayClient)
    worker = MagicMock(spec=IWorkerClient)
    gateway.is_gateway_running.return_value = gateway_running
    gateway.get_active_session.return_value = active_session
    worker.is_on.return_value = worker_on
    worker.is_running.return_value = worker_running
    return DeviceService(gateway=gateway, worker=worker)


class TestDeviceService:
    """Tests for DeviceService combined-check methods."""

    # --- is_device_available ---

    @pytest.mark.parametrize(
        "worker_connected,gateway_running,active_session,worker_busy,expected",
        [
            (True, True, None, False, True),
            (False, True, None, False, False),
            (True, False, None, False, False),
            (True, True, "sess", False, False),
            (True, True, None, True, False),
            (False, False, "sess", True, False),
        ],
    )
    def test_is_device_available(
        self,
        worker_connected,
        gateway_running,
        active_session,
        worker_busy,
        expected,
    ):
        service = _make_service(
            worker_on=worker_connected,
            gateway_running=gateway_running,
            active_session=active_session,
            worker_running=worker_busy,
        )
        assert service.is_device_available() is expected

    # --- check_device_availability ---

    def test_check_device_availability_all_ok(self):
        service = _make_service(
            worker_on=True, gateway_running=True, active_session=None, worker_running=False
        )
        assert service.check_device_availability() is None

    def test_check_device_availability_worker_disconnected(self):
        service = _make_service(worker_on=False)
        result = service.check_device_availability()
        assert result is not None
        assert "worker" in result.lower()

    def test_check_device_availability_gateway_not_running(self):
        service = _make_service(worker_on=True, gateway_running=False)
        result = service.check_device_availability()
        assert result is not None
        assert "gateway" in result.lower()

    def test_check_device_availability_session_active(self):
        service = _make_service(
            worker_on=True, gateway_running=True, active_session={"session_id": "x"}
        )
        result = service.check_device_availability()
        assert result is not None
        assert "sesión" in result.lower()

    def test_check_device_availability_worker_busy(self):
        service = _make_service(
            worker_on=True, gateway_running=True, active_session=None, worker_running=True
        )
        result = service.check_device_availability()
        assert result is not None
        assert "progreso" in result.lower()
