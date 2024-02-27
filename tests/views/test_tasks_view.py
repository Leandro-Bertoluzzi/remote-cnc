import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox

from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from components.cards.MsgCard import MsgCard
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from views.TasksView import TasksView
from core.database.models import Task


class TestTasksView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        task_1 = Task(
            user_id=1,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 1'
        )
        task_2 = Task(
            user_id=1,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 2'
        )
        task_3 = Task(
            user_id=1,
            file_id=1,
            tool_id=1,
            material_id=1,
            name='Example task 3'
        )
        self.tasks_list = [task_1, task_2, task_3]

        # Patch the DB methods
        mocker.patch.object(FileRepository, 'get_all_files_from_user', return_value=[])
        mocker.patch.object(ToolRepository, 'get_all_tools', return_value=[])
        mocker.patch.object(MaterialRepository, 'get_all_materials', return_value=[])

        # Patch the getAllTasksFromUser method with the mock function
        self.mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks_from_user',
            return_value=self.tasks_list
        )

        # Create an instance of TasksView
        self.parent = MainWindow()
        self.tasks_view = TasksView(parent=self.parent)
        qtbot.addWidget(self.tasks_view)

    def test_tasks_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3

    def test_tasks_view_init_with_no_tasks(self, mocker, helpers):
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks_from_user',
            return_value=[]
        )
        tasks_view = TasksView(parent=self.parent)
        # Validate DB calls
        mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0
        assert helpers.count_widgets(tasks_view.layout(), MsgCard) == 1

    @pytest.mark.parametrize(
            'files_error,materials_error,tools_error,tasks_error',
            [
                (False, False, False, True),
                (False, False, True, False),
                (False, True, False, False),
                (True, False, False, False)
            ]
    )
    def test_tasks_view_init_db_error(
        self,
        mocker,
        helpers,
        files_error,
        materials_error,
        tools_error,
        tasks_error
    ):
        mock_get_all_files = mocker.patch.object(
            FileRepository,
            'get_all_files_from_user',
            return_value=[]
        )
        if files_error:
            mock_get_all_files = mocker.patch.object(
                FileRepository,
                'get_all_files_from_user',
                side_effect=Exception('mocked-error')
            )
        mock_get_all_materials = mocker.patch.object(
            MaterialRepository,
            'get_all_materials',
            return_value=[]
        )
        if materials_error:
            mock_get_all_materials = mocker.patch.object(
                MaterialRepository,
                'get_all_materials',
                side_effect=Exception('mocked-error')
            )
        mock_get_all_tools = mocker.patch.object(
            ToolRepository,
            'get_all_tools',
            return_value=[]
        )
        if tools_error:
            mock_get_all_tools = mocker.patch.object(
                ToolRepository,
                'get_all_tools',
                side_effect=Exception('mocked-error')
            )
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks_from_user',
            return_value=[]
        )
        if tasks_error:
            mock_get_all_tasks = mocker.patch.object(
                TaskRepository,
                'get_all_tasks_from_user',
                side_effect=Exception('mocked-error')
            )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Create test view
        tasks_view = TasksView(parent=self.parent)

        # Helper flags
        should_query_materials = not files_error
        should_query_tools = (not materials_error) and should_query_materials
        should_query_tasks = (not tools_error) and should_query_tools

        # Assertions
        assert mock_get_all_files.call_count == 1
        assert mock_get_all_materials.call_count == (1 if should_query_materials else 0)
        assert mock_get_all_tools.call_count == (1 if should_query_tools else 0)
        assert mock_get_all_tasks.call_count == (1 if should_query_tasks else 0)
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(tasks_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0
        assert helpers.count_widgets(tasks_view.layout(), MsgCard) == 0

    def test_tasks_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.tasks_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 2

    def test_tasks_view_refresh_layout_db_error(self, mocker, helpers):
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks_from_user',
            side_effect=[
                self.tasks_list,
                Exception('mocked-error')
            ]
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the method under test
        tasks_view = TasksView(parent=self.parent)
        tasks_view.refreshLayout()

        # Assertions
        assert mock_get_all_tasks.call_count == 2
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(tasks_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(tasks_view.layout(), TaskCard) == 0

    def test_tasks_view_create_task(self, mocker, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, 'Example task 4', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_task(user_id, file_id, tool_id, material_id, name, note):
            task_4 = Task(
                user_id=1,
                file_id=2,
                tool_id=3,
                material_id=4,
                name='Example task 4',
                note='Just a simple description'
            )
            self.tasks_list.append(task_4)
            return

        # Mock and keep track of function calls
        mock_create_task = mocker.patch.object(
            TaskRepository,
            'create_task',
            side_effect=side_effect_create_task
        )

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate DB calls
        assert mock_create_task.call_count == 1
        create_task_params = {
            'user_id': 1,
            'file_id': 2,
            'tool_id': 3,
            'material_id': 4,
            'name': 'Example task 4',
            'note': 'Just a simple description'
        }
        mock_create_task.assert_called_with(*create_task_params.values())
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 4

    def test_tasks_view_create_task_db_error(self, mocker, helpers):
        # Mock TaskDataDialog methods
        mock_inputs = 2, 3, 4, 'Example task 4', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method to simulate exception
        mock_create_task = mocker.patch.object(
            TaskRepository,
            'create_task',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the createTask method
        self.tasks_view.createTask()

        # Validate DB calls
        assert mock_create_task.call_count == 1
        assert self.mock_get_all_tasks.call_count == 1
        assert mock_popup.call_count == 1

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.tasks_view.layout(), MenuButton) == 2
        assert helpers.count_widgets(self.tasks_view.layout(), TaskCard) == 3
