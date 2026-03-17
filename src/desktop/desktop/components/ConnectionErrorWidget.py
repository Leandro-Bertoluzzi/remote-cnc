"""A reusable widget that displays a connection error with retry and back-to-menu actions."""

from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from desktop.components.buttons.MenuButton import MenuButton


class ConnectionErrorWidget(QWidget):
    """Inline widget shown when a view fails to load due to a connection error.

    Displays a friendly error message and provides two action buttons:
    - **Reintentar**: calls ``retry_callback`` to attempt reloading.
    - **Volver al menú**: calls ``back_callback`` to navigate back.
    """

    def __init__(
        self,
        error_message: str,
        retry_callback: Callable[[], None],
        back_callback: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Error icon
        icon_label = QLabel("⚠")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; color: #e74c3c; background: transparent;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Error de conexión")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        layout.addWidget(title_label)

        # Message
        message_label = QLabel(error_message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-size: 14px; color: #cccccc; background: transparent;")
        layout.addWidget(message_label)

        # Spacer
        layout.addSpacing(20)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)

        self.btn_retry = MenuButton("Reintentar", onClick=retry_callback)
        self.btn_back = MenuButton("Volver al menú", onClick=back_callback)

        buttons_layout.addWidget(self.btn_retry)
        buttons_layout.addWidget(self.btn_back)
        layout.addLayout(buttons_layout)
