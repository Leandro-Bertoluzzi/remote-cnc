from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.cards.MaterialCard import MaterialCard
from components.cards.MsgCard import MsgCard
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from components.cards.ToolCard import ToolCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.toolRepository import ToolRepository


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
        if materialDialog.exec():
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

    def showError(self, title, text):
        QMessageBox.critical(self, title, text, QMessageBox.Ok)

    def refreshLayout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            db_session = SessionLocal()
            repository = ToolRepository(db_session)
            tools = repository.get_all_tools()
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        try:
            db_session = SessionLocal()
            repository = MaterialRepository(db_session)
            materials = repository.get_all_materials()
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        # Tools section

        self.layout.addWidget(QLabel('-- HERRAMIENTAS --'))
        self.layout.addWidget(MenuButton('Agregar herramienta', self.createTool))

        for tool in tools:
            self.layout.addWidget(ToolCard(tool, self))

        if not tools:
            self.layout.addWidget(MsgCard('Aún no hay herramientas configuradas', self))

        # Materials section

        self.layout.addWidget(QLabel('-- MATERIALES --'))
        self.layout.addWidget(MenuButton('Agregar material', self.createMaterial))

        for material in materials:
            self.layout.addWidget(MaterialCard(material, self))

        if not materials:
            self.layout.addWidget(MsgCard('Aún no hay materiales configurados', self))

        # Others

        self.layout.addWidget(MenuButton('Volver al menú', self.parent().backToMenu))
        self.update()
