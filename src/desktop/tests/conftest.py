from typing import cast
from unittest.mock import MagicMock

import pytest
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient
from desktop.app_context import AppContext
from desktop.helpers.gatewayMonitor import GatewayMonitor
from desktop.MainWindow import MainWindow
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.fileService import FileService
from desktop.services.materialService import MaterialService
from desktop.services.taskService import TaskService
from desktop.services.toolService import ToolService
from desktop.services.userService import UserService
from desktop.views.BaseListView import BaseListView
from PyQt5.QtWidgets import QGridLayout, QLayout, QWidget
from pytest_mock.plugin import MockerFixture


# Helper fixtures
class Helpers:
    @staticmethod
    def count_widgets(layout: QLayout, widgetType) -> int:
        count = 0
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count

    @staticmethod
    def count_grid_widgets(layout: QGridLayout, widgetType) -> int:
        count = 0
        for index in range(20):
            x, y, *_ = layout.getItemPosition(index)
            if not layout.itemAtPosition(x, y):
                break
            widget = layout.itemAtPosition(x, y).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count


@pytest.fixture
def helpers():
    return Helpers


def make_mock_context() -> AppContext:
    """Return an ``AppContext`` where every port and service is a ``MagicMock``.

    Using this helper avoids ``default_factory`` calls that would try to
    instantiate concrete adapters at import time during tests.
    """
    return AppContext(
        gateway=MagicMock(spec=IGatewayClient),
        worker=MagicMock(spec=IWorkerClient),
        file_storage=MagicMock(spec=IFileStorage),
        session_factory=MagicMock(),
        asset_service=MagicMock(spec=AssetService),
        device_service=MagicMock(spec=DeviceService),
        file_service=MagicMock(spec=FileService),
        material_service=MagicMock(spec=MaterialService),
        task_service=MagicMock(spec=TaskService),
        tool_service=MagicMock(spec=ToolService),
        user_service=MagicMock(spec=UserService),
    )


@pytest.fixture
def mock_context() -> AppContext:
    """Pytest fixture that provides a fully-mocked ``AppContext``."""
    return make_mock_context()


# Mock for UI elements


@pytest.fixture
def mock_window(mocker: MockerFixture):
    """Create a mocked instance of the main window."""
    window = QWidget()
    window.addToolBar = mocker.Mock()
    window.removeToolBar = mocker.Mock()
    window.backToMenu = mocker.Mock()
    window.changeView = mocker.Mock()
    window._on_task_dispatched = mocker.Mock()
    context = make_mock_context()
    window._context = context
    window.gateway_monitor = GatewayMonitor(context.gateway)
    return cast(MainWindow, window)


@pytest.fixture
def mock_view(mocker: MockerFixture):
    """Create a mocked instance of the view containing a widget."""
    view = QWidget()
    view.refreshLayout = mocker.Mock()
    view.showWarning = mocker.Mock()
    view.showError = mocker.Mock()
    view._context = make_mock_context()
    return cast(BaseListView, view)
