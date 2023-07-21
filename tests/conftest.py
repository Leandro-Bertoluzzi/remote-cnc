from PyQt5.QtWidgets import QWidget, QLayout
import os
import pytest

# Set environment variables for tests
os.environ['FILES_FOLDER'] = 'files_folder'
os.environ['USER_ID'] = '1'

class Helpers:
    @staticmethod
    def count_widgets_with_type(layout: QLayout, widgetType: QWidget) -> int:
        count = 0
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, widgetType):
                count = count + 1
        return count

@pytest.fixture
def helpers():
    return Helpers
