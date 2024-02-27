from PyQt5.QtWidgets import QPushButton
from components.cards.Card import Card
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.toolRepository import ToolRepository
from helpers.utils import needs_confirmation


class ToolCard(Card):
    def __init__(self, tool, parent=None):
        super(ToolCard, self).__init__(parent)

        self.tool = tool

        description = f'Herramienta {tool.id}: {tool.name}'
        editToolBtn = QPushButton("Editar")
        editToolBtn.clicked.connect(self.updateTool)
        removeToolBtn = QPushButton("Borrar")
        removeToolBtn.clicked.connect(self.removeTool)

        self.setDescription(description)
        self.addButton(editToolBtn)
        self.addButton(removeToolBtn)

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
        self.parent().refreshLayout()

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
        self.parent().refreshLayout()
