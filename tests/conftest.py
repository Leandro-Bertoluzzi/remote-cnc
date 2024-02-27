from PyQt5.QtWidgets import QLayout, QGridLayout
import pytest


# Helper fixtures
class Helpers:
    @staticmethod
    def count_widgets(layout: QLayout, widgetType) -> int:
        count = 0
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count

    @staticmethod
    def count_grid_widgets(layout: QGridLayout, widgetType) -> int:
        count = 0
        for index in range(20):
            x, y, *_ = layout.getItemPosition(index)
            if not layout.itemAtPosition(x, y):
                break
            widget = layout.itemAtPosition(x, y).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count


@pytest.fixture
def helpers():
    return Helpers
