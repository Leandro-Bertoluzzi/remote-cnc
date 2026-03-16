import pytest
from core.database.models import Task
from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.MsgCard import MsgCard
from desktop.components.cards.TaskCard import TaskCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.MainWindow import MainWindow
from desktop.services.assetService import AssetService
from desktop.services.deviceService import DeviceService
from desktop.services.taskService import TaskService
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

        # Patch the service methods
        mocker.patch.object(AssetService, "get_assets", return_value=([], [], []))

        # Patch the getAllTasksFromUser method with the mock function
        self.mock_get_all_tasks = mocker.patch.object(
            TaskService, "get_all_tasks", return_value=self.tasks_list
        )

        # Patch the constructor of UI components
        mocker.patch.object(TaskCard, "setup_ui")

        # Patch worker/device status checks used by TasksView.getItems()
        mocker.patch.object(DeviceService, "is_device_available", return_value=False)

        # Create an instance of TasksView
        self.parent = mock_window
        self.tasks_view = TasksView(self.parent)
        qtbot.addWidget(self.tasks_view)

    def test_tasks_view_init(self, helpers):
        # Validate service calls
        self.mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3

    def test_tasks_view_init_with_no_tasks(self, mocker: MockerFixture, helpers):
        mock_get_all_tasks = mocker.patch.object(TaskService, "get_all_tasks", return_value=[])
        tasks_view = TasksView(self.parent)
        # Validate service calls
        mock_get_all_tasks.assert_called_once()

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
    def test_tasks_view_init_db_error(self, mocker, helpers, assets_error, tasks_error):
        if assets_error:
            mocker.patch.object(AssetService, "get_assets", side_effect=Exception("mocked-error"))
        mock_get_all_tasks = mocker.patch.object(TaskService, "get_all_tasks", return_value=[])
        if tasks_error:
            mock_get_all_tasks = mocker.patch.object(
                TaskService, "get_all_tasks", side_effect=Exception("mocked-error")
            )

        # Create test view
        tasks_view = TasksView(self.parent)

        # Assertions
        assert helpers.count_widgets(tasks_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0
        assert helpers.count_widgets(tasks_view.layout(), MsgCard) == 0

        if assets_error:
            assert mock_get_all_tasks.call_count == 0
        else:
            assert mock_get_all_tasks.call_count == 1

    def test_tasks_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.tasks_view.refreshLayout()

        # Validate service calls
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 2

    def test_tasks_view_refresh_layout_db_error(self, mocker: MockerFixture, helpers):
        mock_get_all_tasks = mocker.patch.object(
            TaskService,
            "get_all_tasks",
            side_effect=[self.tasks_list, Exception("mocked-error")],
        )

        # Call the method under test
        tasks_view = TasksView(self.parent)
        tasks_view.refreshLayout()

        # Assertions
        assert mock_get_all_tasks.call_count == 2
        assert helpers.count_widgets(tasks_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(tasks_view.layout(), MenuButton) == 1
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0

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

        # Mock and keep track of function calls
        mock_create_task = mocker.patch.object(
            TaskService, "create_task", side_effect=side_effect_create_task
        )

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate service calls
        assert mock_create_task.call_count == 1
        create_task_params = {
            "user_id": 1,
            "file_id": 2,
            "tool_id": 3,
            "material_id": 4,
            "name": "Example task 4",
            "note": "Just a simple description",
        }
        mock_create_task.assert_called_with(*create_task_params.values())
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 4

    def test_tasks_view_create_task_db_error(self, mocker: MockerFixture, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, "Example task 4", "Just a simple description"
        mocker.patch.object(TaskDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, "getInputs", return_value=mock_inputs)

        # Mock service method to simulate exception
        mock_create_task = mocker.patch.object(
            TaskService, "create_task", side_effect=Exception("mocked-error")
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate service calls
        assert mock_create_task.call_count == 1
        assert self.mock_get_all_tasks.call_count == 1
        assert mock_popup.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3
