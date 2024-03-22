import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.RequestCard import RequestCard
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from core.database.models import Task, User, TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
from core.database.repositories.taskRepository import TaskRepository
from helpers.cncWorkerMonitor import CncWorkerMonitor
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from views.RequestsView import RequestsView


class TestRequestCard:
    task = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window):
        mocker.patch.object(RequestsView, 'refreshLayout')

        # Update task
        self.task.id = 1
        self.task.user = User('John Doe', 'john@doe.com', 'password', 'user')

        # Instantiate card
        self.window = mock_window
        self.parent = RequestsView(self.window)
        self.card = RequestCard(self.task, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_request_card_init(self):
        assert self.card.task == self.task
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "msgBoxApprove,msgBoxRun",
            [
                (QMessageBox.Yes, QMessageBox.Yes),
                (QMessageBox.Yes, QMessageBox.No),
                (QMessageBox.Cancel, None)
            ]
        )
    @pytest.mark.parametrize("task_in_progress", [True, False])
    @pytest.mark.parametrize("device_enabled", [True, False])
    def test_request_card_approve_task(
        self,
        mocker: MockerFixture,
        msgBoxApprove,
        msgBoxRun,
        task_in_progress,
        device_enabled
    ):
        # Mock DB methods
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
        mocker.patch.object(
            TaskRepository,
            'are_there_tasks_in_progress',
            return_value=task_in_progress
        )

        # Mock message box methods
        mocker.patch.object(
            QMessageBox,
            'exec',
            side_effect=[msgBoxApprove, msgBoxRun]
        )
        mock_popup = mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)

        # Mock worker monitor methods
        mocker.patch.object(CncWorkerMonitor, 'is_device_enabled', return_value=device_enabled)

        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.RequestCard.send_task_to_worker')

        # Call the approveTask method
        self.card.approveTask()

        # Validate DB calls
        expected_updated = (msgBoxApprove == QMessageBox.Yes)
        assert mock_update_task_status.call_count == (1 if expected_updated else 0)
        if expected_updated:
            update_task_params = {
                'id': 1,
                'status': TASK_APPROVED_STATUS,
                'admin_id': 1,
            }
            mock_update_task_status.assert_called_with(*update_task_params.values())

        # Validate call to tasks manager
        accepted_run = (msgBoxRun == QMessageBox.Yes)
        can_run = not task_in_progress and device_enabled
        expected_run = expected_updated and accepted_run and can_run
        assert mock_add_task_in_queue.call_count == (1 if expected_run else 0)
        assert self.window.startWorkerMonitor.call_count == (1 if expected_run else 0)
        assert mock_popup.call_count == (1 if expected_run else 0)

    @pytest.mark.parametrize(
            'update_error,search_tasks_error',
            [
                (False, True),
                (True, False)
            ]
    )
    def test_request_card_approve_task_db_error(
        self,
        mocker: MockerFixture,
        update_error,
        search_tasks_error
    ):
        # Mock DB methods
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
        if update_error:
            mock_update_task_status = mocker.patch.object(
                TaskRepository,
                'update_task_status',
                side_effect=Exception('mocked error')
            )
        mock_validate_tasks_in_progress = mocker.patch.object(
            TaskRepository,
            'are_there_tasks_in_progress'
        )
        if search_tasks_error:
            mock_validate_tasks_in_progress = mocker.patch.object(
                TaskRepository,
                'are_there_tasks_in_progress',
                side_effect=Exception('mocked error')
            )
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)
        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.RequestCard.send_task_to_worker')

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the approveTask method
        self.card.approveTask()

        # Assertions
        assert mock_update_task_status.call_count == 1
        assert mock_validate_tasks_in_progress.call_count == (0 if update_error else 1)
        assert mock_add_task_in_queue.call_count == 0
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_request_card_reject_task(
        self,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock DB methods
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Call the rejectTask method
        self.card.rejectTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_task_params = {
                'id': 1,
                'status': TASK_REJECTED_STATUS,
                'admin_id': 1,
                'cancellation_reason': 'A valid cancellation reason',
            }
            mock_update_task_status.assert_called_with(*update_task_params.values())

    def test_request_card_reject_task_db_error(self, mocker: MockerFixture):
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Mock DB method to simulate exception
        mock_update_task_status = mocker.patch.object(
            TaskRepository,
            'update_task_status',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the rejectTask method
        self.card.rejectTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == 1
        assert mock_popup.call_count == 1
