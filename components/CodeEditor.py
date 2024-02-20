from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QPainter, QColor, QTextFormat, QPaintEvent, QResizeEvent
from PyQt5.QtWidgets import QPushButton, QFileDialog, QMessageBox, \
    QPlainTextEdit, QTextEdit, QWidget


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event: QPaintEvent):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)

        # State variables
        self.modified = False
        self.file_path = ''

        # Custom UI management
        self.lineNumberArea = LineNumberArea(self)

        # Custom events
        self.textChanged.connect(self.set_modified)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)

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

        file_path, filter = QFileDialog.getOpenFileName(
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
        file_path, filter = QFileDialog.getSaveFileName(
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

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect: QRect, dy: int):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0,
                rect.y(),
                self.lineNumberArea.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self.lineNumberAreaWidth(),
                cr.height()
            )
        )

    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        painter = QPainter(self.lineNumberArea)

        # Line number column background color
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(
                    0,
                    int(top),
                    self.lineNumberArea.width(),
                    height,
                    Qt.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

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
