from components.buttons.MainMenuButton import MainMenuButton, QSvgRenderer, QPainter
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QPaintEvent, QRegion
import pytest
from views.MainMenu import MainMenu


class TestMainMenuButton:
    @pytest.mark.parametrize(
            "image_name",
            [
                'image.png',
                'image.svg'
            ]
        )
    def test_main_menu_button_init(self, qtbot, image_name):
        button = MainMenuButton('Test Button', image_name)
        qtbot.addWidget(button)

        # Assertions
        assert button.text() == 'Test Button'
        assert button.isVisible() is False
        assert hasattr(button, 'renderer') is (image_name == 'image.svg')
        assert button.receivers(button.clicked) == 0
        assert button.sizeHint().height() >= 350
        assert button.sizeHint().width() >= 350

    @pytest.mark.parametrize(
            "image_name,is_hover",
            [
                ('image.png', False),
                ('image.svg', False),
                ('image.png', True),
                ('image.svg', True)
            ]
        )
    def test_main_menu_button_paint_event(self, qtbot, mocker, image_name, is_hover):
        button = MainMenuButton('Test Button', image_name)
        qtbot.addWidget(button)

        # Mock methods
        mock_svg_render = mocker.patch.object(QSvgRenderer, 'render')
        mock_painter_draw_pixmap = mocker.patch.object(QPainter, 'drawPixmap')
        mock_painter_draw_text = mocker.patch.object(QPainter, 'drawText')
        mock_painter_draw_rect = mocker.patch.object(QPainter, 'drawRoundedRect')

        # Mock attributes
        button.hover = is_hover

        # Force event
        region = QRegion(0, 0, 350, 350)
        event = QPaintEvent(region)
        button.paintEvent(event)

        # Assertions
        assert mock_svg_render.call_count == (1 if image_name == 'image.svg' else 0)
        assert mock_painter_draw_pixmap.call_count == (0 if image_name == 'image.svg' else 1)
        assert mock_painter_draw_text.call_count == 1
        assert mock_painter_draw_rect.call_count == (1 if is_hover else 0)

    def test_main_menu_button_hover(self, qtbot):
        button = MainMenuButton('Test Button', 'an-image.png')
        qtbot.addWidget(button)

        # Assertions
        assert button.hover is False

        # Force event
        event = QEvent(QEvent.Enter)
        button.enterEvent(event)
        # Assertions
        assert button.hover is True

        # Force event
        event = QEvent(QEvent.Leave)
        button.leaveEvent(event)
        # Assertions
        assert button.hover is False

    def test_main_menu_button_go_to_view(self, qtbot, mocker):
        parent = MainMenu()
        button = MainMenuButton('Test Button', 'image.png', goToView='Test view', parent=parent)
        qtbot.addWidget(button)

        # Mock parent's method
        mock_main_menu_redirects_to_view = mocker.patch.object(MainMenu, 'redirectToView')

        # User interaction
        button.click()

        # Assertions
        assert mock_main_menu_redirects_to_view.call_count == 1
