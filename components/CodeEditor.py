from components.text.IndexedTextEdit import IndexedTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextFormat, QSyntaxHighlighter, QTextCharFormat, \
    QFont, QTextBlock
from PyQt5.QtWidgets import QPushButton, QFileDialog, QMessageBox, \
    QPlainTextEdit, QTextEdit
import re


class GCodeHighlighter(QSyntaxHighlighter):
    def __init__(self, editor: QPlainTextEdit):
        super().__init__(editor)

        self._mappings: dict[str, QTextCharFormat] = {}
        self.setDocument(editor.document())
        self.setup()

    def add_mapping(self, pattern, format):
        self._mappings[pattern] = format

    def highlightBlock(self, text):
        for pattern, format in self._mappings.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

    def setup(self):
        mword_format = QTextCharFormat()
        mword_format.setFontWeight(QFont.Bold)
        mword_format.setForeground(Qt.green)
        mword_pattern = r'[Mm]\d{1,2}(?=\s|$)'
        self.add_mapping(mword_pattern, mword_format)

        gword_format = QTextCharFormat()
        gword_format.setFontWeight(QFont.Bold)
        gword_format.setForeground(Qt.blue)
        gword_pattern = r'[Gg]\d{1,2}(?=\s|$)'
        self.add_mapping(gword_pattern, gword_format)

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#117506"))
        self.add_mapping(r'\(.+\)', comment_format)
        self.add_mapping(r';.+$', comment_format)

        speed_feed_format = QTextCharFormat()
        speed_feed_format.setForeground(Qt.blue)
        speed_pattern = r'([Ss])\s?\d+'
        feed_pattern = r'([EeFf])\s?\.?\d+(\.\d*)?'
        self.add_mapping(speed_pattern, speed_feed_format)
        self.add_mapping(feed_pattern, speed_feed_format)

        program_format = QTextCharFormat()
        program_format.setForeground(QColor("#69ad4c"))
        line_number_pattern = r'^[N]\d+'
        self.add_mapping(line_number_pattern, program_format)

        xyz_format = QTextCharFormat()
        xyz_format.setForeground(QColor("#b0791a"))
        xyz_pattern = r'[XxYyZz]\s?\-?\d*\.?\d+\.?'
        self.add_mapping(xyz_pattern, xyz_format)

        ijk_format = QTextCharFormat()
        ijk_format.setForeground(QColor("#d4490d"))
        ijk_pattern = r'[IiJjKk]\s?\-?\d*\.?\d+\.?'
        self.add_mapping(ijk_pattern, ijk_format)

        params_format = QTextCharFormat()
        params_format.setForeground(QColor("#8b4cad"))
        radius_pattern = r'[R]\s?\-?\d*\.?\d+\.?'
        dwell_time_pattern = r'[P]\s?\d?\.?\d+\.?'
        tool_pattern = r'[T]\s?\d+'
        self.add_mapping(radius_pattern, params_format)
        self.add_mapping(dwell_time_pattern, params_format)
        self.add_mapping(tool_pattern, params_format)

        grbl_format = QTextCharFormat()
        grbl_format.setFontWeight(QFont.Bold)
        grbl_format.setForeground(Qt.gray)
        grbl_pattern = r'^\$[a-zA-Z\$#]'
        self.add_mapping(grbl_pattern, grbl_format)


class CodeEditor(IndexedTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)

        # State variables
        self.modified = False
        self.file_path = ''

        # Custom UI management
        self.highlighter = GCodeHighlighter(self)
        self.executedLines = 0

        # Custom events
        self.textChanged.connect(self.set_modified)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        # Apply custom styles
        self.setStyleSheet("background-color: 'white';")

    def set_modified(self):
        """Marks the content as modified.
        """
        self.modified = True

    def get_modified(self):
        """Indicates if the content has changes without saving.
        """
        return self.modified

    def get_file_path(self):
        """Returns the path to the open file.
        """
        return self.file_path

    def new_file(self):
        """Empties the editor.
        """
        if self.modified and not self.ask_to_save_changes():
            return

        self.setPlainText('')
        self.modified = False

    # Server FS + DB methods

    def open_file(self):
        """Loads the content of the selected file in the DB.
        """
        pass

    def save_file(self) -> bool:
        """Saves the current text into its corresponding entry in the DB.
        Returns False when the user cancels the action, True otherwise.
        """
        return False

    def save_file_as(self) -> bool:
        """Saves the current text to the selected entry in the DB, or a new one.
        Returns False when the user cancels the action, True otherwise.
        """
        return False

    # Local FS methods

    def import_file(self):
        """Loads the content of the selected file in the local File system.
        """
        if self.modified and not self.ask_to_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar archivo",
            "C:\\",
            "G code files (*.txt *.gcode *.nc)"
        )
        if file_path:
            with open(file_path, "r") as content:
                self.setPlainText(content.read())
                self.modified = False
            self.file_path = file_path

    def export_file(self) -> bool:
        """Saves the current text.
        Returns False when the user cancels the action, True otherwise.
        """
        if not self.file_path:
            return self.export_file_as()

        content = self.toPlainText()
        with open(self.file_path, "w") as file:
            file.write(content)
            self.modified = False
        return True

    def export_file_as(self) -> bool:
        """Saves the current text to the selected file, or a new one.
        Returns False when the user cancels the action, True otherwise.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar archivo",
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
        confirmation.setWindowTitle('Guardar cambios')
        confirmation.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        btnExport = QPushButton('Exportar')
        confirmation.addButton(btnExport, QMessageBox.AcceptRole)
        choice = confirmation.exec()

        if (confirmation.clickedButton() == btnExport):
            return self.export_file()

        if choice == QMessageBox.Yes:
            return self.save_file()
        if choice == QMessageBox.Cancel:
            return False
        return True

    # UI methods

    def indexAreaWidth(self):
        digits = 1
        count = max(1.0, self.blockCount())
        while count >= 10:
            count /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def setIndex(self, block: QTextBlock) -> str:
        return str(block.blockNumber() + 1)

    def setIndexPenColor(self, block: QTextBlock) -> QColor:
        # Font color for lines yet to be executed
        if block.blockNumber() + 1 > self.executedLines:
            return QColor(Qt.black)

        # Font color for already executed lines
        return QColor(Qt.darkYellow)

    def highlightCurrentLine(self):
        if self.isReadOnly():
            return

        selection = QTextEdit.ExtraSelection()
        lineColor = QColor(Qt.yellow).lighter(160)
        selection.format.setBackground(lineColor)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def resetProcessedLines(self):
        self.executedLines = 0
        self.update()

    def markProcessedLines(self, count: int):
        self.executedLines = count
        self.update()
