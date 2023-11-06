from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QAbstractButton
from utils.files import getFileNameInFolder

class MainMenuButton(QAbstractButton):
    def __init__(self, text, imageRelPath, goToView=None, parent=None):
        super(MainMenuButton, self).__init__(parent)

        # Save image
        imagePath = getFileNameInFolder(__file__, imageRelPath).as_posix()
        self.pixmap = QPixmap(imagePath)

        self.setText(text)

        if goToView:
            self.view = goToView
            self.clicked.connect(self.redirectToView)

        stylesheet = getFileNameInFolder(__file__, "MainMenuButton.qss")
        image = getFileNameInFolder(__file__, imageRelPath).as_posix()
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read().replace('{image-url}', image))

    def paintEvent(self, event):
        painter = QPainter(self)

        pen = painter.pen()
        pen.setColor(QColor('#2E1C1C'))
        painter.setPen(pen)

        font = painter.font()
        font.setPixelSize(24)
        painter.setFont(font)

        painter.drawPixmap(event.rect(), self.pixmap)
        painter.drawText(event.rect(), Qt.AlignBottom + Qt.AlignHCenter, self.text())

    def sizeHint(self):
        return self.pixmap.size()

    def redirectToView(self):
        self.parent().redirectToView(self.view)
