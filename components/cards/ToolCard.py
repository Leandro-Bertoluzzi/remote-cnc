from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.dialogs.ToolDataDialog import ToolDataDialog
from database.repositories.toolRepository import updateTool, removeTool

class ToolCard(QWidget):
    def __init__(self, tool, parent=None):
        super(ToolCard, self).__init__(parent)

        self.tool = tool

        toolDescription = QLabel(f'Tarea {tool.id}: {tool.name}')
        editToolBtn = QPushButton("Editar")
        editToolBtn.clicked.connect(self.updateTool)
        removeToolBtn = QPushButton("Borrar")
        removeToolBtn.clicked.connect(self.removeTool)

        layout = QHBoxLayout()
        layout.addWidget(toolDescription)
        layout.addWidget(editToolBtn)
        layout.addWidget(removeToolBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def updateTool(self):
        toolDialog = ToolDataDialog(toolInfo=self.tool)
        if toolDialog.exec():
            name, description = toolDialog.getInputs()
            updateTool(self.tool.id, name, description)
            self.parent().refreshLayout()

    def removeTool(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar la herramienta?')
        confirmation.setWindowTitle('Eliminar herramienta')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            removeTool(self.tool.id)
            self.parent().refreshLayout()
