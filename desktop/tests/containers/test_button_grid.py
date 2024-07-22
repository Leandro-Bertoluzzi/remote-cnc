
from containers.ButtonGrid import ButtonGrid
from PyQt5.QtWidgets import QPushButton


class TestButtonGrid:
    def test_button_grid_init(self, qtbot, mocker, helpers):
        actions = [
            ('Action 1', mocker.Mock()),
            ('Action 2', mocker.Mock()),
            ('Action 3', mocker.Mock()),
            ('Action 4', mocker.Mock())
        ]
        button_grid = ButtonGrid(actions)
        qtbot.addWidget(button_grid)

        # Assertions
        assert helpers.count_widgets(button_grid.layout(), QPushButton) == 4
