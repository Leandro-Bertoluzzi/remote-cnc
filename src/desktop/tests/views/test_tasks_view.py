import pytest
from core.domain.entities import Task
from core.domain.task import TaskStatus
from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.MsgCard import MsgCard
from desktop.components.cards.TaskCard import TaskCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.components.gatewayMonitor import GatewayMonitor
from desktop.MainWindow import MainWindow
from desktop.views.TasksView import TasksView
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestTasksView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        task_1 = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Example task 1")
        task_2 = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Example task 2")
        task_3 = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Example task 3")
        self.tasks_list = [task_1, task_2, task_3]

        # Configure service mocks via context
        mock_window._context.asset_service.get_assets.return_value = ([], [], [])
        mock_window._context.task_service.get_all_tasks.return_value = self.tasks_list
        self.mock_task_service = mock_window._context.task_service
        mock_window._context.device_service.is_device_available.return_value = False

        # Patch the constructor of UI components
        mocker.patch.object(TaskCard, "setup_ui")

        # Create an instance of TasksView
        self.parent = mock_window
        self.tasks_view = TasksView(self.parent)
        qtbot.addWidget(self.tasks_view)

        # Reset call counts accumulated during view creation
        self.parent._context.asset_service.get_assets.reset_mock()
        self.parent._context.task_service.get_all_tasks.reset_mock()

    def test_tasks_view_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3

    def test_tasks_view_init_with_no_tasks(self, helpers):
        self.mock_task_service.get_all_tasks.return_value = []
        tasks_view = TasksView(self.parent)
        # Validate service calls
        self.mock_task_service.get_all_tasks.assert_called()

        # Validate amount of each type of widget
        assert helpers.count_widgets(tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0
        assert helpers.count_widgets(tasks_view.layout(), MsgCard) == 1

    @pytest.mark.parametrize(
        "assets_error,tasks_error",
        [
            (True, False),
            (False, True),
        ],
    )
    def test_tasks_view_init_db_error(self, helpers, assets_error, tasks_error):
        if assets_error:
            self.parent._context.asset_service.get_assets.side_effect = Exception("mocked-error")
        else:
            self.parent._context.asset_service.get_assets.side_effect = None
            self.parent._context.asset_service.get_assets.return_value = ([], [], [])

        if tasks_error:
            self.parent._context.task_service.get_all_tasks.side_effect = Exception("mocked-error")
        else:
            self.parent._context.task_service.get_all_tasks.side_effect = None
            self.parent._context.task_service.get_all_tasks.return_value = []

        # Create test view
        tasks_view = TasksView(self.parent)

        # Assertions
        assert helpers.count_widgets(tasks_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0
        assert helpers.count_widgets(tasks_view.layout(), MsgCard) == 0

        if assets_error:
            assert self.parent._context.task_service.get_all_tasks.call_count == 0
        else:
            assert self.parent._context.task_service.get_all_tasks.call_count == 1

    def test_tasks_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.tasks_view.refreshLayout()

        # Validate service calls
        assert self.mock_task_service.get_all_tasks.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 2

    def test_tasks_view_refresh_layout_db_error(self, helpers):
        self.mock_task_service.get_all_tasks.side_effect = Exception("mocked-error")

        self.tasks_view.refreshLayout()

        assert self.mock_task_service.get_all_tasks.call_count == 1
        assert helpers.count_widgets(self.tasks_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 0

    def test_tasks_view_refresh_layout_assets_error(self, helpers):
        self.parent._context.asset_service.get_assets.side_effect = Exception("mocked-error")

        self.tasks_view.refreshLayout()

        assert self.parent._context.asset_service.get_assets.call_count == 1
        assert self.mock_task_service.get_all_tasks.call_count == 0
        assert helpers.count_widgets(self.tasks_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 0

    def test_tasks_view_create_task(self, mocker: MockerFixture, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, "Example task 4", "Just a simple description"
        mocker.patch.object(TaskDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, "getInputs", return_value=mock_inputs)

        # Mock service method
        def side_effect_create_task(user_id, file_id, tool_id, material_id, name, note):
            task_4 = Task(
                user_id=1,
                file_id=2,
                tool_id=3,
                material_id=4,
                name="Example task 4",
                note="Just a simple description",
            )
            self.tasks_list.append(task_4)
            return

        self.mock_task_service.create_task.side_effect = side_effect_create_task

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate service calls
        assert self.mock_task_service.create_task.call_count == 1
        create_task_params = {
            "user_id": 1,
            "file_id": 2,
            "tool_id": 3,
            "material_id": 4,
            "name": "Example task 4",
            "note": "Just a simple description",
        }
        self.mock_task_service.create_task.assert_called_with(*create_task_params.values())
        assert self.mock_task_service.get_all_tasks.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 4

        # Restore
        self.mock_task_service.create_task.side_effect = None

    def test_tasks_view_create_task_db_error(self, mocker: MockerFixture, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, "Example task 4", "Just a simple description"
        mocker.patch.object(TaskDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, "getInputs", return_value=mock_inputs)

        # Mock service method to simulate exception
        self.mock_task_service.create_task.side_effect = Exception("mocked-error")

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate service calls
        assert self.mock_task_service.create_task.call_count == 1
        assert self.mock_task_service.get_all_tasks.call_count == 0
        assert mock_popup.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3

        # Restore
        self.mock_task_service.create_task.side_effect = None

    # Handler tests

    def test_tasks_view_on_task_run_success(self, qtbot: QtBot, mocker: MockerFixture):
        self.parent._context.device_service.check_device_availability.return_value = None
        self.parent._context.task_service.send_task_to_worker.return_value = "worker-task-id"
        mock_info = mocker.patch.object(QMessageBox, "information", return_value=QMessageBox.Ok)

        task = self.tasks_list[0]
        task.id = 1
        with qtbot.waitSignal(self.tasks_view.task_dispatched, raising=True):
            self.tasks_view.on_task_run(task)

        self.parent._context.task_service.send_task_to_worker.assert_called_once_with(1)
        assert mock_info.call_count == 1

    def test_tasks_view_on_task_run_device_unavailable(self, qtbot: QtBot, mocker: MockerFixture):
        self.parent._context.device_service.check_device_availability.return_value = (
            "Equipo deshabilitado"
        )
        mock_error = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        task = self.tasks_list[0]
        task.id = 1
        with qtbot.assertNotEmitted(self.tasks_view.task_dispatched):
            self.tasks_view.on_task_run(task)

        self.parent._context.task_service.send_task_to_worker.assert_not_called()
        assert mock_error.call_count == 1

    def test_tasks_view_on_task_remove_success(self):
        task = self.tasks_list[0]
        task.id = 1
        self.tasks_view.on_task_remove(task)

        self.parent._context.task_service.remove_task.assert_called_once_with(1)
        assert self.mock_task_service.get_all_tasks.call_count == 1

    def test_tasks_view_on_status_change_success(self):

        task = self.tasks_list[0]
        task.id = 1
        self.tasks_view.on_status_change(task, TaskStatus.APPROVED.value, "")

        self.parent._context.task_service.update_task_status.assert_called_once_with(
            1, TaskStatus.APPROVED.value, 1, ""
        )
        assert self.mock_task_service.get_all_tasks.call_count == 1

    def test_tasks_view_on_pause_resume(self):
        task = self.tasks_list[0]

        self.tasks_view.on_pause_resume(task, True)
        self.parent._context.device_service.request_pause.assert_called_once()

        self.tasks_view.on_pause_resume(task, False)
        self.parent._context.device_service.request_resume.assert_called_once()


class TestTasksViewProgress:
    """Tests for TaskProgress integration inside TasksView."""

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
        mocker.patch.object(GatewayMonitor, "start_monitor")
        self.monitor = mock_window.gateway_monitor

        # Prepare tasks – one in progress
        self.task_running = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Running")
        self.task_running.status = TaskStatus.IN_PROGRESS.value

        self.task_idle = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Idle")

        # Configure service mocks
        mock_window._context.asset_service.get_assets.return_value = ([], [], [])
        mock_window._context.device_service.is_device_available.return_value = True
        mocker.patch.object(TaskCard, "setup_ui")

        self.parent = mock_window

    def _create_view(self, qtbot, tasks):
        self.parent._context.task_service.get_all_tasks.return_value = tasks
        view = TasksView(self.parent, gateway_monitor=self.monitor)
        qtbot.addWidget(view)
        return view

    def test_progress_visible_when_task_in_progress(self, qtbot: QtBot):
        view = self._create_view(qtbot, [self.task_running, self.task_idle])
        assert view.task_progress.isHidden() is False

    def test_progress_hidden_when_no_task_in_progress(self, qtbot: QtBot):
        view = self._create_view(qtbot, [self.task_idle])
        assert view.task_progress.isHidden() is True

    def test_file_progress_signal_updates_bars(self, qtbot: QtBot):
        view = self._create_view(qtbot, [self.task_running])

        # Emit signal
        self.monitor.file_progress.emit(30, 20, 100)

        assert view.task_progress.sent_progress.maximum() == 100
        assert view.task_progress.sent_progress.value() == 30
        assert view.task_progress.process_progress.value() == 20

    def test_file_finished_hides_progress(self, qtbot: QtBot):
        view = self._create_view(qtbot, [self.task_running])
        assert view.task_progress.isHidden() is False

        # After finish, tasks no longer have one in progress
        self.task_running.status = TaskStatus.FINISHED.value
        self.monitor.file_finished.emit()

        assert view.task_progress.isHidden() is True
        assert view._progress_connected is False

    def test_file_failed_hides_progress(self, qtbot: QtBot, mocker: MockerFixture):
        view = self._create_view(qtbot, [self.task_running])
        assert view.task_progress.isHidden() is False

        self.task_running.status = TaskStatus.FAILED.value
        self.monitor.file_failed.emit("Some error")

        assert view.task_progress.isHidden() is True
        assert view._progress_connected is False

    def test_close_event_disconnects_signals(self, qtbot: QtBot, mocker: MockerFixture):
        view = self._create_view(qtbot, [self.task_running])
        assert view._progress_connected is True

        view.close()

        assert view._progress_connected is False
