from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QTextEdit
from PyQt5.QtCore import Qt

FROM_CANCEL = 'cancel'
FROM_REJECT = 'reject'


class TaskCancelDialog(QDialog):
    def __init__(self, origin=FROM_CANCEL, parent=None):
        super(TaskCancelDialog, self).__init__(parent)

        layout = QFormLayout(self)

        self.note = QTextEdit(self)
        noteLabel = 'Razón de cancelación' if origin == FROM_CANCEL else 'Razón de rechazo'
        layout.addRow(noteLabel, self.note)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        title = 'Cancelar tarea' if origin == FROM_CANCEL else 'Rechazar tarea'
        self.setWindowTitle(title)

    def getInput(self):
        return self.note.toPlainText()
