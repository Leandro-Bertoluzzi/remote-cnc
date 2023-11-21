from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.cards.MaterialCard import MaterialCard
from components.cards.MsgCard import MsgCard
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from components.cards.ToolCard import ToolCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.utils.database import create_tool, get_all_tools, create_material, get_all_materials


class InventoryView(QWidget):
    def __init__(self, parent=None):
        super(InventoryView, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.refreshLayout()

        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

    def createTool(self):
        toolDialog = ToolDataDialog()
        if toolDialog.exec():
            name, description = toolDialog.getInputs()
            create_tool(name, description)
            self.refreshLayout()

    def createMaterial(self):
        materialDialog = MaterialDataDialog()
        if materialDialog.exec():
            name, description = materialDialog.getInputs()
            create_material(name, description)
            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Tools section

        self.layout.addWidget(QLabel('-- HERRAMIENTAS --'))
        self.layout.addWidget(MenuButton('Agregar herramienta', self.createTool))

        tools = get_all_tools()
        for tool in tools:
            self.layout.addWidget(ToolCard(tool, self))

        if not tools:
            self.layout.addWidget(MsgCard('Aún no hay herramientas configuradas', self))

        # Materials section

        self.layout.addWidget(QLabel('-- MATERIALES --'))
        self.layout.addWidget(MenuButton('Agregar material', self.createMaterial))

        materials = get_all_materials()
        for material in materials:
            self.layout.addWidget(MaterialCard(material, self))

        if not materials:
            self.layout.addWidget(MsgCard('Aún no hay materiales configurados', self))

        # Others

        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()
