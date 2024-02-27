from PyQt5.QtWidgets import QPushButton, QMessageBox
from components.cards.Card import Card
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.toolRepository import ToolRepository


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
        if toolDialog.exec():
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

    def removeTool(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar la herramienta?')
        confirmation.setWindowTitle('Eliminar herramienta')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
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
