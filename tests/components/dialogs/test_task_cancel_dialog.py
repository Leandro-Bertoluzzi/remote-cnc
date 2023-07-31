import pytest
from components.dialogs.TaskCancelDialog import TaskCancelDialog, FROM_CANCEL, FROM_REJECT

class TestTaskCancelDialog:
    @pytest.mark.parametrize(
            "origin,expected_title",
            [
                (FROM_CANCEL, 'Cancelar tarea'),
                (FROM_REJECT, 'Rechazar tarea')
            ]
        )
    def test_task_data_dialog_init(self, qtbot, origin, expected_title):
        dialog = TaskCancelDialog(origin)
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None
        assert dialog.windowTitle() == expected_title

    def test_task_data_dialog_get_input(self, qtbot):
        dialog = TaskCancelDialog()
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.note.setPlainText('A valid cancellation reason')

        assert dialog.getInput() == 'A valid cancellation reason'
