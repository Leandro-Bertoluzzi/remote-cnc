from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout
from utils.config import suppressQtWarnings

class MainMenu(QDialog):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Top'))
        layout.addWidget(QPushButton('Bottom'))
        self.setLayout(layout)
        self.setWindowTitle("Example")

if __name__ == '__main__':
    suppressQtWarnings()
    import sys

    app = QApplication(sys.argv)
    gallery = MainMenu()
    gallery.show()
    sys.exit(app.exec())