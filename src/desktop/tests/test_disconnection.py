"""Tests that verify the ConnectionErrorWidget is displayed when services fail.

These tests validate the core resilience requirement: when external services
(DB, Redis, Celery) are unavailable, the app shows an inline error widget
with retry and back-to-menu buttons instead of crashing or showing empty views.
"""

from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.TaskCard import TaskCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.MainWindow import MainWindow
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.fileService import FileService
from desktop.services.materialService import MaterialService
from desktop.services.taskService import TaskService
from desktop.services.toolService import ToolService
from desktop.services.userService import UserService
from desktop.views.FilesView import FilesView
from desktop.views.InventoryView import InventoryView
from desktop.views.TasksView import TasksView
from desktop.views.UsersView import UsersView
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestConnectionErrorWidget:
    """Test the ConnectionErrorWidget itself."""

    def test_widget_shows_message(self, qtbot: QtBot):
        widget = ConnectionErrorWidget(
            "Test error message", retry_callback=lambda: None, back_callback=lambda: None
        )
        qtbot.addWidget(widget)

        # Just check the widget was created and has buttons
        assert widget.btn_retry is not None
        assert widget.btn_back is not None

    def test_widget_retry_callback(self, qtbot: QtBot, mocker: MockerFixture):
        mock_retry = mocker.Mock()
        widget = ConnectionErrorWidget(
            "Error", retry_callback=mock_retry, back_callback=lambda: None
        )
        qtbot.addWidget(widget)

        # Click retry button
        widget.btn_retry.click()
        mock_retry.assert_called_once()

    def test_widget_back_callback(self, qtbot: QtBot, mocker: MockerFixture):
        mock_back = mocker.Mock()
        widget = ConnectionErrorWidget(
            "Error", retry_callback=lambda: None, back_callback=mock_back
        )
        qtbot.addWidget(widget)

        # Click back button
        widget.btn_back.click()
        mock_back.assert_called_once()


class TestDisconnectionTasksView:
    """Test that TasksView shows ConnectionErrorWidget on service failures."""

    def test_assets_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(
            AssetService, "get_assets", side_effect=Exception("DB connection refused")
        )
        mocker.patch.object(TaskCard, "setup_ui")

        view = TasksView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), TaskCard) == 0

    def test_task_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(AssetService, "get_assets", return_value=([], [], []))
        mocker.patch.object(TaskCard, "setup_ui")
        mocker.patch.object(
            TaskService, "get_all_tasks", side_effect=Exception("DB connection refused")
        )
        mocker.patch.object(DeviceService, "is_device_available", return_value=False)

        view = TasksView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), TaskCard) == 0


class TestDisconnectionFilesView:
    """Test that FilesView shows ConnectionErrorWidget on service failure."""

    def test_file_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(
            FileService, "get_all_files", side_effect=Exception("DB connection refused")
        )

        view = FilesView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), MenuButton) == 1


class TestDisconnectionUsersView:
    """Test that UsersView shows ConnectionErrorWidget on service failure."""

    def test_user_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(
            UserService, "get_all_users", side_effect=Exception("DB connection refused")
        )

        view = UsersView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), MenuButton) == 1


class TestDisconnectionInventoryView:
    """Test that InventoryView shows ConnectionErrorWidget on service failure."""

    def test_tool_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(
            ToolService, "get_all_tools", side_effect=Exception("DB connection refused")
        )

        view = InventoryView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1

    def test_material_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mocker.patch.object(ToolService, "get_all_tools", return_value=[])
        mocker.patch.object(
            MaterialService, "get_all_materials", side_effect=Exception("DB connection refused")
        )

        view = InventoryView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1


class TestDisconnectionMainWindow:
    """Test that MainWindow.changeView shows ConnectionErrorWidget on failure."""

    def test_change_view_failure_shows_error(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock the worker status calls in MainWindow.__init__
        mocker.patch.object(DeviceService, "is_worker_connected", return_value=False)
        # Mock closeEvent to prevent actual window closing during tests
        mocker.patch.object(MainWindow, "closeEvent", lambda self, event: event.accept())

        window = MainWindow()
        qtbot.addWidget(window)

        # Simulate a view constructor that raises
        def failing_view(parent):
            raise Exception("DB connection refused")

        failing_view.__name__ = "FailingView"

        window.changeView(failing_view) # type: ignore[arg-type]

        # Should show ConnectionErrorWidget in the central widget
        central = window.centralWidget()
        assert isinstance(central, ConnectionErrorWidget)
