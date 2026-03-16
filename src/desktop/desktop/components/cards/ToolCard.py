from core.database.models import Tool
from desktop.components.cards.Card import Card
from desktop.components.dialogs.ToolDataDialog import ToolDataDialog
from desktop.helpers.utils import needs_confirmation
from desktop.services.toolService import ToolService


class ToolCard(Card):
    def __init__(self, tool: Tool, parent=None):
        super(ToolCard, self).__init__(parent)

        self.tool = tool
        self.setup_ui()

    def setup_ui(self):
        description = f"Herramienta {self.tool.id}: {self.tool.name}"
        self.setDescription(description)

        self.addButton("Editar", self.updateTool)
        self.addButton("Borrar", self.removeTool)

    def updateTool(self):
        toolDialog = ToolDataDialog(toolInfo=self.tool)
        if not toolDialog.exec():
            return

        name, description = toolDialog.getInputs()
        try:
            ToolService.update_tool(self.tool.id, name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()

    @needs_confirmation("¿Realmente desea eliminar la herramienta?", "Eliminar herramienta")
    def removeTool(self):
        try:
            ToolService.remove_tool(self.tool.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()
