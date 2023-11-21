from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPlainTextEdit


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)

        # State variables
        self.modified = False
        self.file_path = ''

        # Custom events
        self.textChanged.connect(self.set_modified)

        # Apply custom styles
        self.setStyleSheet("background-color: 'white';")

    def set_modified(self):
        """Marks the content as modified.
        """
        self.modified = True

    def new_file(self):
        """Empties the editor.
        """
        if self.modified and not self.ask_to_save_changes():
            return

        self.setPlainText('')
        self.modified = False

    def open_file(self):
        """Loads the content of the selected file.
        """
        if self.modified and not self.ask_to_save_changes():
            return

        file_path, filter = QFileDialog.getOpenFileName(
            self,
            "Select a File",
            "C:\\",
            "G code files (*.txt *.gcode *.nc)"
        )
        if file_path:
            with open(file_path, "r") as content:
                self.setPlainText(content.read())
                self.modified = False
            self.file_path = file_path

    def save_file(self) -> bool:
        """Saves the current text.
        Returns False when the user cancels the action, True otherwise.
        """
        if not self.file_path:
            return self.save_file_as()

        content = self.toPlainText()
        with open(self.file_path, "w") as file:
            file.write(content)
            self.modified = False
        return True

    def save_file_as(self) -> bool:
        """Saves the current text to the selected file.
        Returns False when the user cancels the action, True otherwise.
        """
        file_path, filter = QFileDialog.getSaveFileName(
            self,
            "Select a File",
            "C:\\",
            "G code files (*.txt *.gcode *.nc)"
        )
        if file_path:
            content = self.toPlainText()
            with open(file_path, "w") as file:
                file.write(content)
                self.modified = False
            self.file_path = file_path
            return True
        return False

    def ask_to_save_changes(self) -> bool:
        """Asks to the user if they want to save the changes before continuing.
        Returns False when the user cancels the action, True otherwise.
        """
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Desea guardar el avance primero?')
        confirmation.setWindowTitle('Abrir archivo')
        confirmation.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        choice = confirmation.exec()

        if choice == QMessageBox.Yes:
            return self.save_file()
        if choice == QMessageBox.Cancel:
            return False
        return True
