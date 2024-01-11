from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QCursor, QPaintEvent
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QAbstractButton
from core.utils.files import getFileNameInFolder

color_text = QColor('#2E1C1C')
color_hover_border = QColor('black')
color_hover_fill = QColor('#555555')
color_hover_text = QColor('#6e0e0e')


class MainMenuButton(QAbstractButton):
    def __init__(self, text, imageRelPath, goToView=None, parent=None):
        super(MainMenuButton, self).__init__(parent)

        # Save image
        self.imagePath = getFileNameInFolder(__file__, imageRelPath).as_posix()

        # Customize painter
        self.pixmap = QPixmap(self.imagePath)
        if self.imagePath.endswith('.svg'):
            self.renderer = QSvgRenderer(self.imagePath)

        # Customize button
        self.setText(text)
        self.setMinimumSize(350, 350)
        self.setMaximumSize(350, 350)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.hover = False

        # Button action
        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)

    def paintEvent(self, event: QPaintEvent):
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
            painter.drawRoundedRect(event.rect(), 15, 15)

        pen.setColor(color_text)
        if self.hover:
            pen.setColor(color_hover_text)
        painter.setPen(pen)

        if self.imagePath.endswith('.svg'):
            self.renderer.render(painter)
        else:
            painter.drawPixmap(event.rect(), self.pixmap)

        painter.drawText(event.rect(), Qt.AlignBottom + Qt.AlignHCenter, self.text())

    def enterEvent(self, event: QEvent):
        self.hover = True
        event.accept()

    def leaveEvent(self, event: QEvent):
        self.hover = False
        event.accept()

    def sizeHint(self):
        return self.size()

    def redirectToView(self):
        self.parent().redirectToView(self.view)
