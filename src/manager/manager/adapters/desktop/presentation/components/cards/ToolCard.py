from core.domain.entities import Tool
from manager.adapters.desktop.presentation.components.cards.Card import Card
from manager.adapters.desktop.presentation.components.dialogs.ToolDataDialog import ToolDataDialog
from manager.adapters.desktop.presentation.components.utils import needs_confirmation
from PyQt5.QtCore import pyqtSignal


class ToolCard(Card):
    """Presentation-only card for a Tool entity."""

    # (tool, name, description)
    update_requested = pyqtSignal(object, str, str)
    # (tool,)
    remove_requested = pyqtSignal(object)

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
        self.update_requested.emit(self.tool, name, description)

    @needs_confirmation("¿Realmente desea eliminar la herramienta?", "Eliminar herramienta")
    def removeTool(self):
        self.remove_requested.emit(self.tool)
