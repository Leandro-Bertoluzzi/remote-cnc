from components.cards.Card import Card
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.database.base import SessionLocal
from core.database.models import Tool
from core.database.repositories.toolRepository import ToolRepository
from helpers.utils import needs_confirmation


class ToolCard(Card):
    def __init__(self, tool: Tool, parent=None):
        super(ToolCard, self).__init__(parent)

        self.tool = tool
        self.setup_ui()

    def setup_ui(self):
        description = f'Herramienta {self.tool.id}: {self.tool.name}'
        self.setDescription(description)

        self.addButton("Editar", self.updateTool)
        self.addButton("Borrar", self.removeTool)

    def updateTool(self):
        toolDialog = ToolDataDialog(toolInfo=self.tool)
        if not toolDialog.exec():
            return

        name, description = toolDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = ToolRepository(db_session)
            repository.update_tool(self.tool.id, name, description)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar la herramienta?', 'Eliminar herramienta')
    def removeTool(self):
        try:
            db_session = SessionLocal()
            repository = ToolRepository(db_session)
            repository.remove_tool(self.tool.id)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()
