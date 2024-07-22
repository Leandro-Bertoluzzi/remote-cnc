from abc import abstractmethod
from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QColor, QPainter, QPaintEvent, QResizeEvent, QTextBlock
from PyQt5.QtWidgets import QPlainTextEdit, QWidget


class IndexArea(QWidget):
    def __init__(self, editor: 'IndexedTextEdit'):
        super().__init__(editor)
        self.textEditor = editor

    def sizeHint(self):
        return QSize(self.textEditor.indexAreaWidth(), 0)

    def paintEvent(self, event: QPaintEvent):
        self.textEditor.indexAreaPaintEvent(event)


class IndexedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(IndexedTextEdit, self).__init__(parent)

        # Custom UI management
        self.indexArea = IndexArea(self)

        # Custom events
        self.blockCountChanged.connect(self.updateIndexAreaWidth)
        self.updateRequest.connect(self.updateIndexArea)

        # Initialize UI
        self.updateIndexAreaWidth(0)

        # Apply custom styles
        self.setStyleSheet("background-color: 'white';")

    # UI methods

    def updateIndexAreaWidth(self, _):
        self.setViewportMargins(self.indexAreaWidth(), 0, 0, 0)

    def updateIndexArea(self, rect: QRect, dy: int):
        if dy:
            self.indexArea.scroll(0, dy)
        else:
            self.indexArea.update(
                0,
                rect.y(),
                self.indexArea.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.updateIndexAreaWidth(0)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.indexArea.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self.indexAreaWidth(),
                cr.height()
            )
        )

    def indexAreaPaintEvent(self, event: QPaintEvent):
        painter = QPainter(self.indexArea)

        # Line number column background color
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()

        # Draw indexes
        while block.isValid() and (top <= event.rect().bottom()):
            pen_color = self.setIndexPenColor(block)
            painter.setPen(pen_color)

            if block.isVisible() and (bottom >= event.rect().top()):
                index = self.setIndex(block)
                painter.drawText(
                    0,
                    int(top),
                    self.indexArea.width(),
                    height,
                    Qt.AlignRight,
                    index
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

    # Abstract methods

    @abstractmethod
    def indexAreaWidth(self):
        raise NotImplementedError    # pragma: no cover

    @abstractmethod
    def setIndex(self, block: QTextBlock) -> str:
        raise NotImplementedError    # pragma: no cover

    @abstractmethod
    def setIndexPenColor(self, block: QTextBlock) -> QColor:
        raise NotImplementedError    # pragma: no cover
