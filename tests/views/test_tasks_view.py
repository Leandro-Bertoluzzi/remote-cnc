import pytest
from PyQt5.QtWidgets import QDialogButtonBox

from MainWindow import MainWindow
from components.MenuButton import MenuButton
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
from views.TasksView import TasksView
from database.models.task import Task

class TestTasksView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        task_1 = Task(
            user_id=USER_ID,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 1'
        )
        task_2 = Task(
            user_id=USER_ID,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 2'
        )
        task_3 = Task(
            user_id=USER_ID,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 3'
        )
        self.tasks_list = [task_1, task_2, task_3]

        # Patch the DB methods
        mocker.patch('views.TasksView.getAllFilesFromUser', return_value=[])
        mocker.patch('views.TasksView.getAllTools', return_value=[])
        mocker.patch('views.TasksView.getAllMaterials', return_value=[])

        # Patch the getAllTasksFromUser method with the mock function
        self.mock_get_all_tasks = mocker.patch('views.TasksView.getAllTasksFromUser', return_value=self.tasks_list)

        # Create an instance of TasksView
        self.parent = MainWindow()
        self.tasks_view = TasksView(parent=self.parent)
        qtbot.addWidget(self.tasks_view)

    def test_tasks_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.tasks_view.layout, MenuButton) == 2
        assert helpers.count_widgets_with_type(self.tasks_view.layout, TaskCard) == 3

    def test_tasks_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.tasks_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.tasks_view.layout, MenuButton) == 2
        assert helpers.count_widgets_with_type(self.tasks_view.layout, TaskCard) == 2

    def test_tasks_view_create_task(self, mocker, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, 'Example task 4', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_task(user_id, file_id, tool_id, material_id, name, note):
            task_4 = Task(
                user_id=USER_ID,
                file_id=2,
                tool_id=3,
                material_id=4,
                name='Example task 4',
                note='Just a simple description'
            )
            self.tasks_list.append(task_4)
            return

        # Mock and keep track of function calls
        mock_create_task = mocker.patch('views.TasksView.createTask', side_effect=side_effect_create_task)
        mock_add_task_in_queue = mocker.patch('views.TasksView.addTask.delay')

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate DB calls
        assert mock_create_task.call_count == 1
        create_task_params = {
            'user_id': USER_ID,
            'file_id': 2,
            'tool_id': 3,
            'material_id': 4,
            'name': 'Example task 4',
            'note': 'Just a simple description'
        }
        mock_create_task.assert_called_with(*create_task_params.values())
        assert self.mock_get_all_tasks.call_count == 2

        # Validate call to tasks manager
        assert mock_add_task_in_queue.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.tasks_view.layout, MenuButton) == 2
        assert helpers.count_widgets_with_type(self.tasks_view.layout, TaskCard) == 4
