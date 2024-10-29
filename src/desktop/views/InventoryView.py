from desktop.components.cards.MaterialCard import MaterialCard
from desktop.components.dialogs.MaterialDataDialog import MaterialDataDialog
from desktop.components.cards.ToolCard import ToolCard
from desktop.components.dialogs.ToolDataDialog import ToolDataDialog
from database.base import SessionLocal
from database.repositories.materialRepository import MaterialRepository
from database.repositories.toolRepository import ToolRepository
from desktop.views.BaseListView import BaseListView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class InventoryView(BaseListView):
    def __init__(self, parent: 'MainWindow'):
        super(InventoryView, self).__init__(parent)

        self.setItemListFromValues(
            'HERRAMIENTAS',
            'Aún no hay herramientas configuradas',
            self.createToolCard,
            'Agregar herramienta',
            self.createTool
        )
        self.setItemListFromValues(
            'MATERIALES',
            'Aún no hay materiales configurados',
            self.createMaterialCard,
            'Agregar material',
            self.createMaterial
        )
        self.refreshLayout()

    def createToolCard(self, item):
        return ToolCard(item, self)

    def createMaterialCard(self, item):
        return MaterialCard(item, self)

    def getItems(self):
        if self.current_index == 0:
            return self.getTools()
        return self.getMaterials()

    def getTools(self):
        db_session = SessionLocal()
        repository = ToolRepository(db_session)
        return repository.get_all_tools()

    def getMaterials(self):
        db_session = SessionLocal()
        repository = MaterialRepository(db_session)
        return repository.get_all_materials()

    def createTool(self):
        toolDialog = ToolDataDialog()
        if not toolDialog.exec():
            return

        name, description = toolDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = ToolRepository(db_session)
            repository.create_tool(name, description)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.refreshLayout()

    def createMaterial(self):
        materialDialog = MaterialDataDialog()
        if not materialDialog.exec():
            return

        name, description = materialDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = MaterialRepository(db_session)
            repository.create_material(name, description)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.refreshLayout()
