import pytest
from core.domain.entities import Task
from core.domain.task import TaskStatus
from desktop.presentation.components.cards.TaskCard import TaskCard
from desktop.presentation.components.dialogs.TaskCancelDialog import TaskCancelDialog
from desktop.presentation.components.dialogs.TaskDataDialog import TaskDataDialog
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestTaskCard:
    task = Task(user_id=1, file_id=1, tool_id=1, material_id=1, name="Example task")

    @pytest.fixture(scope="function")
    def setup_method(self, qtbot: QtBot, mock_view):
        self.task.id = 1
        self.parent = mock_view
        self.card = TaskCard(self.task, False, [], [], [], parent=self.parent)
        qtbot.addWidget(self.card)

    @pytest.mark.parametrize(
        "status,expected_buttons",
        [
            ("pending_approval", 3),
            ("on_hold", 2),
            ("in_progress", 1),
            ("finished", 1),
            ("failed", 1),
            ("cancelled", 2),
        ],
    )
    def test_task_card_init(self, qtbot: QtBot, helpers, status, expected_buttons):
        self.task.status = status
        self.task.id = 1

        card = TaskCard(self.task, False, [], [], [])
        qtbot.addWidget(card)

        assert card.task == self.task
        assert card.layout() is not None
        assert helpers.count_widgets(card.layout_buttons, QPushButton) == expected_buttons

    def test_task_card_init_device_busy(self, qtbot: QtBot):
        self.task.status = TaskStatus.ON_HOLD.value
        self.task.id = 1

        card = TaskCard(self.task, True, [], [], [])
        qtbot.addWidget(card)

        while card.layout().count():
            child = card.layout().takeAt(0)
            if isinstance(child.widget(), QPushButton):
                assert child.widget().isEnabled() is False

    @pytest.mark.parametrize("dialogResponse", [QDialog.Accepted, QDialog.Rejected])
    def test_task_card_update_task(self, setup_method, mocker: MockerFixture, dialogResponse):
        mock_input = 2, 3, 4, "Updated task", "Just a simple description"
        mocker.patch.object(TaskDataDialog, "__init__", return_value=None)
        mocker.patch.object(TaskDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.update_requested.connect(handler)

        self.card.updateTask()

        if dialogResponse == QDialog.Accepted:
            handler.assert_called_once_with(
                self.task, 2, 3, 4, "Updated task", "Just a simple description"
            )
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize(
        "msgBoxResponse,expected_emitted", [(QMessageBox.Yes, True), (QMessageBox.Cancel, False)]
    )
    def test_task_card_remove_task(
        self, setup_method, mocker: MockerFixture, msgBoxResponse, expected_emitted
    ):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.remove_requested.connect(handler)

        self.card.removeTask()

        if expected_emitted:
            handler.assert_called_once_with(self.task)
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("msgBoxResponse", [QMessageBox.Yes, QMessageBox.Cancel])
    def test_task_card_restore_task(self, setup_method, mocker: MockerFixture, msgBoxResponse):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.status_change_requested.connect(handler)

        self.card.restoreTask()

        expected_emitted = msgBoxResponse == QMessageBox.Yes
        if expected_emitted:
            handler.assert_called_once_with(self.task, TaskStatus.INITIAL.value, "")
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("dialogResponse", [QDialog.Accepted, QDialog.Rejected])
    def test_task_card_cancel_task(self, setup_method, mocker: MockerFixture, dialogResponse):
        mock_input = "A valid cancellation reason"
        mocker.patch.object(TaskCancelDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(TaskCancelDialog, "getInput", return_value=mock_input)

        handler = mocker.Mock()
        self.card.status_change_requested.connect(handler)

        self.card.cancelTask()

        if dialogResponse == QDialog.Accepted:
            handler.assert_called_once_with(
                self.task, TaskStatus.CANCELLED.value, "A valid cancellation reason"
            )
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("dialogResponse", [QDialog.Accepted, QDialog.Rejected])
    def test_task_card_repeat_task(self, setup_method, mocker: MockerFixture, dialogResponse):
        mock_input = 2, 3, 4, "Repeated task", "Just a simple description"
        mocker.patch.object(TaskDataDialog, "__init__", return_value=None)
        mocker.patch.object(TaskDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.repeat_requested.connect(handler)

        self.card.repeatTask()

        if dialogResponse == QDialog.Accepted:
            handler.assert_called_once_with(
                self.task, 2, 3, 4, "Repeated task", "Just a simple description"
            )
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("msgBoxRun", [QMessageBox.Yes, QMessageBox.Cancel])
    def test_task_card_run_task(self, setup_method, mocker: MockerFixture, msgBoxRun):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxRun)

        handler = mocker.Mock()
        self.card.run_requested.connect(handler)

        self.card.runTask()

        if msgBoxRun == QMessageBox.Yes:
            handler.assert_called_once_with(self.task)
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("msgBoxApprove", [QMessageBox.Yes, QMessageBox.Cancel])
    def test_task_card_approve_task(self, setup_method, mocker: MockerFixture, msgBoxApprove):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxApprove)

        handler = mocker.Mock()
        self.card.status_change_requested.connect(handler)

        self.card.approveTask()

        if msgBoxApprove == QMessageBox.Yes:
            handler.assert_called_once_with(self.task, TaskStatus.APPROVED.value, "")
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("paused", [False, True])
    def test_task_card_pause_task(self, setup_method, mocker: MockerFixture, paused):
        self.card.paused = paused

        handler = mocker.Mock()
        self.card.pause_resume_requested.connect(handler)

        self.card.pauseTask()

        handler.assert_called_once_with(self.task, paused)
        # State should be toggled after emit
        assert self.card.paused == (not paused)
