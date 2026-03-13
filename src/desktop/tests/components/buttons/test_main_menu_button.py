from desktop.components.buttons.MainMenuButton import MainMenuButton, QSvgRenderer, QPainter
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QPaintEvent, QRegion
from PyQt5.QtWidgets import QWidget
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMainMenuButton:
    @pytest.mark.parametrize(
            "image_name",
            [
                'image.png',
                'image.svg'
            ]
        )
    def test_main_menu_button_init(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        image_name
    ):
        # Mock SVG creation
        mocker.patch.object(QSvgRenderer, '__init__', return_value=None)

        # Create test button
        button = MainMenuButton('Test Button', image_name)
        qtbot.addWidget(button)

        # Assertions
        assert button.text() == 'Test Button'
        assert button.isVisible() is False
        assert hasattr(button, 'renderer') is (image_name == 'image.svg')
        assert button.receivers(button.clicked) == 0

    @pytest.mark.parametrize(
            "image_name,is_hover",
            [
                ('image.png', False),
                ('image.svg', False),
                ('image.png', True),
                ('image.svg', True)
            ]
        )
    def test_main_menu_button_paint_event(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        image_name,
        is_hover
    ):
        # Mock SVG creation
        mocker.patch.object(QSvgRenderer, '__init__', return_value=None)

        # Create test button
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

    def test_main_menu_button_hover(self, qtbot: QtBot):
        # Create test button
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

    def test_main_menu_button_go_to_view(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock parent
        parent = QWidget()
        parent.redirectToView = mocker.Mock()

        # Instantiate button
        button = MainMenuButton('Test Button', 'image.png', goToView='Test view', parent=parent)
        qtbot.addWidget(button)

        # User interaction
        button.click()

        # Assertions
        parent.redirectToView.assert_called_once()
