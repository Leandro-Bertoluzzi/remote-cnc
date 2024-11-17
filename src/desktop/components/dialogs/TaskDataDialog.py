from database.models import File, Material, Task, Tool
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, QTextEdit
from PyQt5.QtCore import Qt
from typing import Optional


class TaskDataDialog(QDialog):
    def __init__(
            self,
            files: list[File]=[],
            tools: list[Tool]=[],
            materials: list[Material]=[],
            taskInfo: Optional[Task]=None,
            parent=None
        ):
        super(TaskDataDialog, self).__init__(parent)

        self.files = files
        self.tools = tools
        self.materials = materials

        fileNames = [file.file_name for file in files]
        toolNames = [tool.name for tool in tools]
        materialNames = [material.name for material in materials]

        self.name = QLineEdit(self)
        self.file = QComboBox(self)
        self.file.addItems(fileNames)
        self.tool = QComboBox(self)
        self.tool.addItems(toolNames)
        self.material = QComboBox(self)
        self.material.addItems(materialNames)
        self.note = QTextEdit(self)

        if taskInfo:
            self.name.setText(taskInfo.name)
            self.file.setCurrentIndex(fileNames.index(taskInfo.file.file_name))
            self.tool.setCurrentIndex(toolNames.index(taskInfo.tool.name))
            self.material.setCurrentIndex(materialNames.index(taskInfo.material.name))
            self.note.setPlainText(taskInfo.note)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        layout = QFormLayout(self)
        layout.addRow('Nombre', self.name)
        layout.addRow('Archivo', self.file)
        layout.addRow('Herramienta', self.tool)
        layout.addRow('Material', self.material)
        layout.addRow('Nota adicional (opcional)', self.note)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Crear tarea' if not taskInfo else 'Actualizar tarea')

    def getInputs(self):
        return (
            self.files[self.file.currentIndex()].id,
            self.tools[self.tool.currentIndex()].id,
            self.materials[self.material.currentIndex()].id,
            self.name.text(),
            self.note.toPlainText()
        )


class TaskFromFileDialog(TaskDataDialog):
    def __init__(
            self,
            file: File,
            tools: list[Tool]=[],
            materials: list[Material]=[],
            parent=None
        ):
        super(TaskFromFileDialog, self).__init__([file], tools, materials, None, parent)

        self.file.setEnabled(False)
        self.setWindowTitle('Crear tarea')
