from components.buttons.MenuButton import MenuButton
from components.cards.MsgCard import MsgCard
from components.cards.RequestCard import RequestCard
from core.database.models import Task, User
from core.database.repositories.taskRepository import TaskRepository
from MainWindow import MainWindow
from PyQt5.QtWidgets import QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from views.RequestsView import RequestsView


class TestRequestsView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window: MainWindow):
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
        self.mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks',
            return_value=self.tasks_list
        )

        # Create an instance of RequestsView
        self.parent = mock_window
        self.requests_view = RequestsView(self.parent)
        qtbot.addWidget(self.requests_view)

    def test_requests_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.requests_view.layout(), MenuButton) == 1
        assert helpers.count_widgets(self.requests_view.layout(), RequestCard) == 3

    def test_requests_view_init_with_no_requests(self, mocker: MockerFixture, helpers):
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks',
            return_value=[]
        )
        requests_view = RequestsView(self.parent)
        # Validate DB calls
        mock_get_all_tasks.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets(requests_view.layout(), MenuButton) == 1
        assert helpers.count_widgets(requests_view.layout(), RequestCard) == 0
        assert helpers.count_widgets(requests_view.layout(), MsgCard) == 1

    def test_requests_view_init_db_error(self, mocker: MockerFixture, helpers):
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks',
            side_effect=Exception('mocked-error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Create test view
        requests_view = RequestsView(self.parent)

        # Assertions
        mock_get_all_tasks.assert_called_once()
        mock_popup.assert_called_once()
        assert helpers.count_widgets(requests_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(requests_view.layout(), RequestCard) == 0
        assert helpers.count_widgets(requests_view.layout(), MsgCard) == 0

    def test_requests_view_refresh_layout(self, helpers):
        # We remove a task
        self.tasks_list.pop()

        # Call the refreshLayout method
        self.requests_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_tasks.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets(self.requests_view.layout(), MenuButton) == 1
        assert helpers.count_widgets(self.requests_view.layout(), RequestCard) == 2

    def test_requests_view_refresh_layout_db_error(self, mocker: MockerFixture, helpers):
        # Mock DB methods to simulate error(s)
        # 1st execution: Widget creation (needs to success)
        # 2nd execution: Test case
        mock_get_all_tasks = mocker.patch.object(
            TaskRepository,
            'get_all_tasks',
            side_effect=[
                self.tasks_list,
                Exception('mocked-error')
            ]
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the method under test
        requests_view = RequestsView(self.parent)
        requests_view.refreshLayout()

        # Assertions
        assert mock_get_all_tasks.call_count == 2
        assert mock_popup.call_count == 1
        assert helpers.count_widgets(requests_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(requests_view.layout(), RequestCard) == 0
