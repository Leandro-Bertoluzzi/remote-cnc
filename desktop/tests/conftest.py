from MainWindow import MainWindow
from PyQt5.QtWidgets import QLayout, QGridLayout, QWidget
import pytest
from pytest_mock.plugin import MockerFixture
from typing import cast
from views.BaseListView import BaseListView


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

# Mock for UI elements


@pytest.fixture
def mock_window(mocker: MockerFixture):
    """Create a mocked instance of the main window.
    """
    parent = QWidget()
    parent.addToolBar = mocker.Mock()
    parent.removeToolBar = mocker.Mock()
    parent.backToMenu = mocker.Mock()
    parent.changeView = mocker.Mock()
    parent.startWorkerMonitor = mocker.Mock()
    return cast(MainWindow, parent)


@pytest.fixture
def mock_view(mocker: MockerFixture):
    """Create a mocked instance of the view containing a widget.
    """
    parent = QWidget()
    parent.refreshLayout = mocker.Mock()
    parent.showWarning = mocker.Mock()
    parent.showError = mocker.Mock()
    return cast(BaseListView, parent)
