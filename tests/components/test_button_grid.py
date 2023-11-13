
from components.ButtonGrid import ButtonGrid
from PyQt5.QtWidgets import QPushButton

class TestButtonGrid:
    def test_button_grid_init(self, qtbot, helpers):
        actions = ['Action 1', 'Action 2', 'Action 3', 'Action 4']
        button_grid = ButtonGrid(actions)
        qtbot.addWidget(button_grid)

        # Assertions
        assert helpers.count_widgets_with_type(button_grid.layout(), QPushButton) == 4
