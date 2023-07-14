from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from components.MenuButton import MenuButton
from components.cards.MaterialCard import MaterialCard
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from components.cards.ToolCard import ToolCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from database.repositories.toolRepository import createTool, getAllTools
from database.repositories.materialRepository import createMaterial, getAllMaterials

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
            createTool(name, description)
            self.refreshLayout()

    def createMaterial(self):
        materialDialog = MaterialDataDialog()
        if materialDialog.exec():
            name, description = materialDialog.getInputs()
            createMaterial(name, description)
            self.refreshLayout()

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Tools section

        self.layout.addWidget(QLabel('-- HERRAMIENTAS --'))
        self.layout.addWidget(MenuButton('Agregar herramienta', self.createTool))

        tools = getAllTools()
        for tool in tools:
            self.layout.addWidget(ToolCard(tool, self))

        # Materials section

        self.layout.addWidget(QLabel('-- MATERIALES --'))
        self.layout.addWidget(MenuButton('Agregar material', self.createMaterial))

        materials = getAllMaterials()
        for material in materials:
            self.layout.addWidget(MaterialCard(material, self))

        # Others

        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()
