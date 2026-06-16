from typing import TYPE_CHECKING

from desktop.presentation.components.cards.MaterialCard import MaterialCard
from desktop.presentation.components.cards.ToolCard import ToolCard
from desktop.presentation.components.dialogs.MaterialDataDialog import MaterialDataDialog
from desktop.presentation.components.dialogs.ToolDataDialog import ToolDataDialog
from desktop.presentation.views.BaseListView import BaseListView

if TYPE_CHECKING:
    from desktop.presentation.MainWindow import MainWindow  # pragma: no cover


class InventoryView(BaseListView):
    def __init__(self, parent: "MainWindow", **kwargs):
        super(InventoryView, self).__init__(parent, **kwargs)

        self.setItemListFromValues(
            "HERRAMIENTAS",
            "Aún no hay herramientas configuradas",
            self.createToolCard,
            "Agregar herramienta",
            self.createTool,
        )
        self.setItemListFromValues(
            "MATERIALES",
            "Aún no hay materiales configurados",
            self.createMaterialCard,
            "Agregar material",
            self.createMaterial,
        )
        self.refreshLayout()

    def createToolCard(self, item):
        card = ToolCard(item, self)
        card.update_requested.connect(self.on_tool_update)
        card.remove_requested.connect(self.on_tool_remove)
        return card

    def createMaterialCard(self, item):
        card = MaterialCard(item, self)
        card.update_requested.connect(self.on_material_update)
        card.remove_requested.connect(self.on_material_remove)
        return card

    def getItems(self):
        if self.current_index == 0:
            return self.getTools()
        return self.getMaterials()

    def getTools(self):
        return self._context.tool_service.get_all_tools()

    def getMaterials(self):
        return self._context.material_service.get_all_materials()

    def createTool(self):
        toolDialog = ToolDataDialog()
        if not toolDialog.exec():
            return

        name, description = toolDialog.getInputs()
        try:
            self._context.tool_service.create_tool(name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    def createMaterial(self):
        materialDialog = MaterialDataDialog()
        if not materialDialog.exec():
            return

        name, description = materialDialog.getInputs()
        try:
            self._context.material_service.create_material(name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    # Signal handlers

    def on_tool_update(self, tool, name, description):
        if tool.id is None:
            return

        try:
            self._context.tool_service.update_tool(tool.id, name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    def on_tool_remove(self, tool):
        if tool.id is None:
            return

        try:
            self._context.tool_service.remove_tool(tool.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    # Signal handlers

    def on_material_update(self, material, name, description):
        if material.id is None:
            return

        try:
            self._context.material_service.update_material(material.id, name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()

    def on_material_remove(self, material):
        if material.id is None:
            return

        try:
            self._context.material_service.remove_material(material.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.refreshLayout()
