from MainWindow import MainWindow
from views.MainMenu import MainMenu
from views.UsersView import UsersView
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMessageBox
import pytest


class TestMainWindow:
    def test_main_window_init(self, qtbot):
        window = MainWindow()
        qtbot.addWidget(window)

        assert type(window.centralWidget()) is MainMenu
        assert window.windowTitle() == "CNC admin"

    def test_main_window_changes_view(self, qtbot, mocker):
        window = MainWindow()
        qtbot.addWidget(window)

        # Test changing view to 'users'
        mocker.patch.object(UsersView, 'refreshLayout')
        window.changeView(UsersView)
        assert type(window.centralWidget()) is UsersView

        # Test going back to the main menu
        window.backToMenu()
        assert type(window.centralWidget()) is MainMenu

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_main_window_close_event(
        self,
        qtbot,
        mocker,
        msgBoxResponse,
        expectedMethodCalls
    ):
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock QMessageBox method
        mock_popup = mocker.patch.object(
            QMessageBox,
            'question',
            return_value=msgBoxResponse
        )

        # Mock child widget method
        mock_child_close_event = mocker.patch.object(window.centralWidget(), 'closeEvent')

        # Call method under test
        window.closeEvent(QCloseEvent())

        # Assertions
        assert mock_popup.call_count == 1
        assert mock_child_close_event.call_count == expectedMethodCalls
