"""Tests that verify the ConnectionErrorWidget is displayed when services fail.

These tests validate the core resilience requirement: when external services
(DB, Redis, Worker) are unavailable, the app shows an inline error widget
with retry and back-to-menu buttons instead of crashing or showing empty views.
"""

from desktop.presentation.components.buttons.MenuButton import MenuButton
from desktop.presentation.components.cards.TaskCard import TaskCard
from desktop.presentation.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.presentation.MainWindow import MainWindow
from desktop.presentation.views.FilesView import FilesView
from desktop.presentation.views.InventoryView import InventoryView
from desktop.presentation.views.TasksView import TasksView
from desktop.presentation.views.UsersView import UsersView
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot

from desktop.tests.conftest import make_mock_context


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
        mock_window._context.asset_service.get_assets.side_effect = Exception(
            "DB connection refused"
        )
        mocker.patch.object(TaskCard, "setup_ui")

        view = TasksView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), TaskCard) == 0

    def test_task_service_failure_shows_error(
        self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow, helpers
    ):
        mock_window._context.asset_service.get_assets.return_value = ([], [], [])
        mock_window._context.asset_service.get_assets.side_effect = None
        mocker.patch.object(TaskCard, "setup_ui")
        mock_window._context.task_service.get_all_tasks.side_effect = Exception(
            "DB connection refused"
        )
        mock_window._context.device_service.is_device_available.return_value = False

        view = TasksView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), TaskCard) == 0


class TestDisconnectionFilesView:
    """Test that FilesView shows ConnectionErrorWidget on service failure."""

    def test_file_service_failure_shows_error(self, qtbot: QtBot, mock_window: MainWindow, helpers):
        mock_window._context.file_service.get_all_files.side_effect = Exception(
            "DB connection refused"
        )

        view = FilesView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), MenuButton) == 0


class TestDisconnectionUsersView:
    """Test that UsersView shows ConnectionErrorWidget on service failure."""

    def test_user_service_failure_shows_error(self, qtbot: QtBot, mock_window: MainWindow, helpers):
        mock_window._context.user_service.get_all_users.side_effect = Exception(
            "DB connection refused"
        )

        view = UsersView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(view.layout(), MenuButton) == 0


class TestDisconnectionInventoryView:
    """Test that InventoryView shows ConnectionErrorWidget on service failure."""

    def test_tool_service_failure_shows_error(self, qtbot: QtBot, mock_window: MainWindow, helpers):
        mock_window._context.tool_service.get_all_tools.side_effect = Exception(
            "DB connection refused"
        )

        view = InventoryView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1

    def test_material_service_failure_shows_error(
        self, qtbot: QtBot, mock_window: MainWindow, helpers
    ):
        mock_window._context.tool_service.get_all_tools.return_value = []
        mock_window._context.tool_service.get_all_tools.side_effect = None
        mock_window._context.material_service.get_all_materials.side_effect = Exception(
            "DB connection refused"
        )

        view = InventoryView(mock_window)
        qtbot.addWidget(view)

        assert helpers.count_widgets(view.layout(), ConnectionErrorWidget) == 1


class TestDisconnectionMainWindow:
    """Test that MainWindow.changeView shows ConnectionErrorWidget on failure."""

    def test_change_view_failure_shows_error(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock closeEvent to prevent actual window closing during tests
        mocker.patch.object(MainWindow, "closeEvent", lambda self, event: event.accept())

        context = make_mock_context()
        context.device_service.is_worker_connected.return_value = False
        window = MainWindow(context)
        qtbot.addWidget(window)

        # Simulate a view constructor that raises
        def failing_view(parent):
            raise Exception("DB connection refused")

        failing_view.__name__ = "FailingView"

        window.changeView(failing_view)

        # Should show ConnectionErrorWidget in the central widget
        central = window.centralWidget()
        assert isinstance(central, ConnectionErrorWidget)
