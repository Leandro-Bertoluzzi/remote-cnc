from core.utilities.files import getFileNameInFolder
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPaintEvent, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QAbstractButton

color_text = QColor("#2E1C1C")
color_hover_border = QColor("black")
color_hover_fill = QColor("#555555")
color_hover_text = QColor("#6e0e0e")
button_size = 240


class MainMenuButton(QAbstractButton):
    def __init__(self, text, imageRelPath, goToView=None, parent=None):
        super(MainMenuButton, self).__init__(parent)

        # Save image
        self.imagePath = getFileNameInFolder(__file__, imageRelPath).as_posix()

        # Customize painter
        self.pixmap = QPixmap(self.imagePath)
        if self.imagePath.endswith(".svg"):
            self.renderer = QSvgRenderer(self.imagePath)

        # Customize button
        self.setText(text)
        self.setMinimumSize(button_size, button_size)
        self.setMaximumSize(button_size, button_size)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.hover = False

        # Button action
        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)

    def paintEvent(self, e: QPaintEvent) -> None:
        painter = QPainter(self)

        pen = painter.pen()
        pen.setColor(color_hover_border)
        pen.setWidth(5)
        painter.setPen(pen)

        brush = painter.brush()
        brush.setColor(color_hover_fill)
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        font = painter.font()
        font.setPixelSize(24)
        font.setBold(True)
        painter.setFont(font)

        if self.hover:
            painter.drawRoundedRect(e.rect(), 15, 15)

        pen.setColor(color_text)
        if self.hover:
            pen.setColor(color_hover_text)
        painter.setPen(pen)

        if self.imagePath.endswith(".svg"):
            self.renderer.render(painter)
        else:
            painter.drawPixmap(e.rect(), self.pixmap)

        painter.drawText(e.rect(), Qt.AlignBottom + Qt.AlignHCenter, self.text())

    def enterEvent(self, a0: QEvent) -> None:
        self.hover = True
        a0.accept()

    def leaveEvent(self, a0: QEvent) -> None:
        self.hover = False
        a0.accept()

    def sizeHint(self):
        return self.size()

    def redirectToView(self):
        parent = self.parent()
        if parent is not None:
            parent.redirectToView(self.view)  # type: ignore[attr-defined]
