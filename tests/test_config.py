import os
from config import suppressQtWarnings, Globals


def test_suppressQtWarnings():
    # Call the function under test
    suppressQtWarnings()

    # Check if environment variables are set correctly
    assert os.getenv("QT_DEVICE_PIXEL_RATIO") == "0"
    assert os.getenv("QT_AUTO_SCREEN_SCALE_FACTOR") == "1"
    assert os.getenv("QT_SCREEN_SCALE_FACTORS") == "1"
    assert os.getenv("QT_SCALE_FACTOR") == "1"


class TestGlobals:
    def test_set_get_current_task_id(self):
        assert Globals.get_current_task_id() != 'my-task-id'
        Globals.set_current_task_id('my-task-id')
        assert Globals.get_current_task_id() == 'my-task-id'
