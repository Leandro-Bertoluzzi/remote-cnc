import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.RequestCard import RequestCard
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from database.models.task import Task, TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
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
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(RequestsView, 'refreshLayout')

        self.parent = RequestsView()
        self.task.id = 1
        self.card = RequestCard(self.task, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_request_card_init(self):
        assert self.card.task == self.task
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "msgBoxResponse,expected_updated",
            [
                (QMessageBox.Yes, True),
                (QMessageBox.Cancel, False)
            ]
        )
    @pytest.mark.parametrize("task_in_progress", [True, False])
    def test_request_card_approve_task(self, mocker, msgBoxResponse, expected_updated, task_in_progress):
        # Mock DB methods
        mock_update_task_status = mocker.patch('components.cards.RequestCard.updateTaskStatus')
        mocker.patch('components.cards.RequestCard.areThereTasksInProgress', return_value=task_in_progress)
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)
        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.RequestCard.executeTask.delay')

        # Call the approveTask method
        self.card.approveTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == (1 if expected_updated else 0)
        if expected_updated:
            update_task_params = {
                'id': 1,
                'status': TASK_APPROVED_STATUS,
                'admin_id': 1,
            }
            mock_update_task_status.assert_called_with(*update_task_params.values())

        # Validate call to tasks manager
        expected_call_to_worker = expected_updated and not task_in_progress
        assert mock_add_task_in_queue.call_count == (1 if expected_call_to_worker else 0)

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_request_card_reject_task(self, mocker, dialogResponse, expected_updated):
        # Mock DB methods
        mock_update_task_status = mocker.patch('components.cards.RequestCard.updateTaskStatus')
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
