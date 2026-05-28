import pytest
from core.domain.entities import File, User
from desktop.components.cards.FileCard import FileCard
from desktop.components.dialogs.FileDataDialog import FileDataDialog
from desktop.components.dialogs.TaskDataDialog import TaskFromFileDialog
from PyQt5.QtWidgets import QDialog, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestFileCard:
    file = File(user_id=1, file_name="example_file.gcode", file_hash="hashed-file")
    user_test = User(name="test_user", email="test@email.com", password="password", role="admin")

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        self.file.id = 1
        self.file.user = self.user_test
        self.parent = mock_view
        self.card = FileCard(self.file, [], [], parent=self.parent)
        qtbot.addWidget(self.card)

    def test_file_card_init(self):
        description = self.card.label_description
        assert self.card.file == self.file
        assert description.text() == "Archivo 1: example_file.gcode\nUsuario: test_user"
        assert self.card.layout is not None

    @pytest.mark.parametrize(
        "dialogResponse,expected_emitted", [(QDialog.Accepted, True), (QDialog.Rejected, False)]
    )
    def test_file_card_update_file(self, mocker: MockerFixture, dialogResponse, expected_emitted):
        mock_input = "updated_name.gcode", "path/to/file.gcode"
        mocker.patch.object(FileDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(FileDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.rename_requested.connect(handler)

        self.card.updateFile()

        if expected_emitted:
            handler.assert_called_once_with(self.file, "updated_name.gcode")
        else:
            handler.assert_not_called()

    def test_file_card_update_file_no_change(self, mocker: MockerFixture):
        mock_input = "example_file.gcode", "path/to/example_file.gcode"
        mocker.patch.object(FileDataDialog, "exec", return_value=QDialog.Accepted)
        mocker.patch.object(FileDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.rename_requested.connect(handler)

        self.card.updateFile()

        handler.assert_not_called()

    @pytest.mark.parametrize(
        "msgBoxResponse,expected_emitted", [(QMessageBox.Yes, True), (QMessageBox.Cancel, False)]
    )
    def test_file_card_remove_file(self, mocker: MockerFixture, msgBoxResponse, expected_emitted):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.remove_requested.connect(handler)

        self.card.removeFile()

        if expected_emitted:
            handler.assert_called_once_with(self.file)
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("dialogResponse", [QDialog.Accepted, QDialog.Rejected])
    def test_file_card_create_task_from_file(self, mocker: MockerFixture, dialogResponse):
        mock_input = 1, 2, 3, "task name", "note"
        mocker.patch.object(TaskFromFileDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(TaskFromFileDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.create_task_requested.connect(handler)

        self.card.createTaskFromFile()

        if dialogResponse == QDialog.Accepted:
            handler.assert_called_once_with(self.file, 2, 3, "task name", "note")
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize("dialogResponse", [QDialog.Accepted, QDialog.Rejected])
    def test_file_card_execute_task_from_file(self, mocker: MockerFixture, dialogResponse):
        mock_input = 1, 2, 3, "task name", "note"
        mocker.patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes)
        mocker.patch.object(TaskFromFileDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(TaskFromFileDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.execute_task_requested.connect(handler)

        self.card.executeTaskFromFile()

        if dialogResponse == QDialog.Accepted:
            handler.assert_called_once_with(self.file, 2, 3, "task name", "note")
        else:
            handler.assert_not_called()

    def test_file_card_execute_task_confirmation_rejected(self, mocker: MockerFixture):
        mocker.patch.object(QMessageBox, "exec", return_value=QMessageBox.No)

        handler = mocker.Mock()
        self.card.execute_task_requested.connect(handler)

        self.card.executeTaskFromFile()

        handler.assert_not_called()
