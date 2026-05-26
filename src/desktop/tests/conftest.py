from typing import cast
from unittest.mock import MagicMock

import pytest
from core.ports.file_storage import IFileStorage
from core.ports.gateway_client import IGatewayClient
from core.ports.worker_client import IWorkerClient
from desktop.app_context import AppContext
from desktop.helpers.gatewayMonitor import GatewayMonitor
from desktop.MainWindow import MainWindow
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
    """Return an ``AppContext`` where every port is a ``MagicMock``.

    Using this helper avoids ``default_factory`` calls that would try to
    instantiate concrete adapters at import time during tests.
    """
    return AppContext(
        gateway=MagicMock(spec=IGatewayClient),
        worker=MagicMock(spec=IWorkerClient),
        file_storage=MagicMock(spec=IFileStorage),
        session_factory=MagicMock(),
    )


@pytest.fixture
def mock_context() -> AppContext:
    """Pytest fixture that provides a fully-mocked ``AppContext``."""
    return make_mock_context()


# Mock for UI elements


@pytest.fixture
def mock_window(mocker: MockerFixture):
    """Create a mocked instance of the main window."""
    parent = QWidget()
    parent.addToolBar = mocker.Mock()
    parent.removeToolBar = mocker.Mock()
    parent.backToMenu = mocker.Mock()
    parent.changeView = mocker.Mock()
    parent.startWorkerMonitor = mocker.Mock()
    context = make_mock_context()
    parent._context = context
    parent.worker_monitor = GatewayMonitor(context.gateway)
    return cast(MainWindow, parent)


@pytest.fixture
def mock_view(mocker: MockerFixture):
    """Create a mocked instance of the view containing a widget."""
    parent = QWidget()
    parent.refreshLayout = mocker.Mock()
    parent.showWarning = mocker.Mock()
    parent.showError = mocker.Mock()
    return cast(BaseListView, parent)
