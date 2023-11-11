import os
from config import Globals

class TestGlobals:
    def test_set_get_current_task_id(self):
        assert Globals.get_current_task_id() is not 'my-task-id'
        Globals.set_current_task_id('my-task-id')
        assert Globals.get_current_task_id() is 'my-task-id'
