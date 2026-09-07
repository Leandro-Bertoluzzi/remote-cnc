import pytest
from core.domain.entities import Tool
from manager.adapters.desktop.presentation.components.cards.ToolCard import ToolCard
from manager.adapters.desktop.presentation.components.dialogs.ToolDataDialog import ToolDataDialog
from PyQt5.QtWidgets import QDialog, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestToolCard:
    tool = Tool(name="Example tool", description="Just a tool")

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        self.tool.id = 1
        self.parent = mock_view
        self.card = ToolCard(self.tool, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_tool_card_init(self):
        assert self.card.tool == self.tool
        assert self.card.layout is not None

    @pytest.mark.parametrize(
        "dialogResponse,expected_emitted", [(QDialog.Accepted, True), (QDialog.Rejected, False)]
    )
    def test_tool_card_update_tool(self, mocker: MockerFixture, dialogResponse, expected_emitted):
        mock_input = "Updated tool", "Updated description"
        mocker.patch.object(ToolDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(ToolDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.update_requested.connect(handler)

        self.card.updateTool()

        if expected_emitted:
            handler.assert_called_once_with(self.tool, "Updated tool", "Updated description")
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize(
        "msgBoxResponse,expected_emitted", [(QMessageBox.Yes, True), (QMessageBox.Cancel, False)]
    )
    def test_tool_card_remove_tool(self, mocker: MockerFixture, msgBoxResponse, expected_emitted):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.remove_requested.connect(handler)

        self.card.removeTool()

        if expected_emitted:
            handler.assert_called_once_with(self.tool)
        else:
            handler.assert_not_called()
