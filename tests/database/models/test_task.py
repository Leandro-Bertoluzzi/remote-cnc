from database.models.task import Task
from datetime import datetime

def test_task():
    # Auxiliary variables
    now = datetime(2023, 7, 20)

    # Instantiate task
    task = Task(
        user_id=1,
        file_id=2,
        tool_id=3,
        material_id=4,
        name='Example task',
        note='Just a task',
        status='on_hold',
        priority=8,
        created_at=now
    )

    # Validate task fields
    assert task.user_id == 1
    assert task.file_id == 2
    assert task.tool_id == 3
    assert task.material_id == 4
    assert task.name == 'Example task'
    assert task.status == 'on_hold'
    assert task.note == 'Just a task'
    assert task.priority == 8
    assert task.created_at == datetime(2023, 7, 20)

    assert task.__repr__() == '<Task: Example task, status: on_hold, created at: 2023-07-20 00:00:00>'

def test_task_default_values():
    # Auxiliary variables
    now = datetime(2023, 7, 20)

    # Instantiate task
    task = Task(
        user_id=1,
        file_id=2,
        tool_id=3,
        material_id=4,
        name='Example task',
        created_at=now
    )

    # Validate task fields
    assert task.user_id == 1
    assert task.file_id == 2
    assert task.tool_id == 3
    assert task.material_id == 4
    assert task.name == 'Example task'
    assert task.note == ''
    assert task.status == 'pending_approval'
    assert task.priority == 0
    assert task.created_at == datetime(2023, 7, 20)

    assert task.__repr__() == '<Task: Example task, status: pending_approval, created at: 2023-07-20 00:00:00>'

