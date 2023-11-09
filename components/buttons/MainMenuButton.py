from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QCursor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QAbstractButton
from utils.files import getFileNameInFolder

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
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.hover = False

        # Button action
        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)

    def paintEvent(self, event):
        painter = QPainter(self)

        pen = painter.pen()
        pen.setColor(QColor('black'))
        pen.setWidth(5)
        painter.setPen(pen)

        brush = painter.brush()
        brush.setColor(QColor('#555555'))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        font = painter.font()
        font.setPixelSize(24)
        font.setBold(True)
        painter.setFont(font)

        if self.hover:
            painter.drawRoundedRect(event.rect(), 15, 15)

        pen.setColor(QColor('#2E1C1C'))
        painter.setPen(pen)

        if self.imagePath.endswith('.svg'):
            self.renderer.render(painter)
        else:
            painter.drawPixmap(event.rect(), self.pixmap)

        painter.drawText(event.rect(), Qt.AlignBottom + Qt.AlignHCenter, self.text())

    def enterEvent(self, event):
        self.hover = True

    def leaveEvent(self, event):
        self.hover = False

    def sizeHint(self):
        return self.size()

    def redirectToView(self):
        self.parent().redirectToView(self.view)
