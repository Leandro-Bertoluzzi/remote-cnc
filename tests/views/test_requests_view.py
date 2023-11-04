import pytest
from PyQt5.QtWidgets import QDialogButtonBox

from MainWindow import MainWindow
from components.buttons.MenuButton import MenuButton
from components.cards.RequestCard import RequestCard
from views.RequestsView import RequestsView
from database.models.task import Task
from database.models.user import User

class TestRequestsView:
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

        task_1.user = User('John Doe', 'john@doe.com', 'password', 'user')
        task_2.user = User('John Doe', 'john@doe.com', 'password', 'user')
        task_3.user = User('John Doe', 'john@doe.com', 'password', 'user')
        self.tasks_list = [task_1, task_2, task_3]

        # Patch the getAllTasksFromUser method with the mock function
        self.mock_get_all_tasks = mocker.patch('views.RequestsView.get_all_tasks', return_value=self.tasks_list)

        # Create an instance of RequestsView
        self.parent = MainWindow()
        self.requests_view = RequestsView(parent=self.parent)
        qtbot.addWidget(self.requests_view)

    def test_requests_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.requests_view.layout, MenuButton) == 1
        assert helpers.count_widgets_with_type(self.requests_view.layout, RequestCard) == 3

    def test_requests_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.requests_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.requests_view.layout, MenuButton) == 1
        assert helpers.count_widgets_with_type(self.requests_view.layout, RequestCard) == 2
