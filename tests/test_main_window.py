from helpers.cncWorkerMonitor import CncWorkerMonitor
from MainWindow import MainWindow
from views.MainMenu import MainMenu
from views.UsersView import UsersView
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMainWindow:
    @pytest.mark.parametrize("worker_on", [False, True])
    def test_main_window_init(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        worker_on
    ):
        # Mock worker monitor methods
        mocker.patch.object(CncWorkerMonitor, 'is_worker_on', return_value=worker_on)

        # Mock QMessageBox method
        mocker.patch.object(
            QMessageBox,
            'question',
            return_value=QMessageBox.Yes
        )

        # Instantiate window
        window = MainWindow()
        qtbot.addWidget(window)

        # Assertions
        assert type(window.centralWidget()) is MainMenu
        assert window.windowTitle() == "CNC admin"
        expected_worker_status = 'Worker : CONECTADO' if worker_on else 'Worker : DESCONECTADO'
        assert window.status_bar.label_worker.text() == expected_worker_status

    def test_main_window_changes_view(self, qtbot: QtBot, mocker: MockerFixture):
        # Instantiate window
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock QMessageBox method
        mocker.patch.object(
            QMessageBox,
            'question',
            return_value=QMessageBox.Yes
        )

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
        qtbot: QtBot,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Instantiate window
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock QMessageBox method
        mock_popup = mocker.patch.object(
            QMessageBox,
            'question',
            return_value=msgBoxResponse
        )

        # Mock child widget method
        mock_child_close_event = mocker.patch.object(
            window.centralWidget(),
            'closeEvent'
        )

        # Call method under test
        window.closeEvent(QCloseEvent())

        # Assertions
        assert mock_popup.call_count == 1
        assert mock_child_close_event.call_count == expectedMethodCalls
