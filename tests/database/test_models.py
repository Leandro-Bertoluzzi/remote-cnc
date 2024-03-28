from conftest import created_time
from database.repositories.fileRepository import FileRepository
from database.repositories.materialRepository import MaterialRepository
from database.repositories.taskRepository import TaskRepository
from database.repositories.toolRepository import ToolRepository
from database.repositories.userRepository import UserRepository


def test_task(mocked_session):
    # Get test task
    task_repository = TaskRepository(mocked_session)
    task = task_repository.get_task_by_id(1)

    # Call methods under test
    serialized_task = task.serialize()
    task_str = repr(task)

    # Assertions
    assert serialized_task == {
        'id': 1,
        'name': 'Task 1',
        'status': 'pending_approval',
        'priority': 0,
        'user_id': 1,
        'user': 'User 1',
        'file_id': 1,
        'file': 'file-1.gcode',
        'tool_id': 1,
        'tool': 'tool 1',
        'material_id': 1,
        'material': 'material 1',
        'note': 'This is a note',
        'created_at': created_time,
        'status_updated_at': created_time,
        'admin_id': None,
        'admin': '',
        'cancellation_reason': None
    }

    assert task_str == '<Task: Task 1, status: pending_approval, created at: 2023-12-25 00:00:00>'


def test_file(mocked_session):
    # Get test file
    file_repository = FileRepository(mocked_session)
    file = file_repository.get_file_by_id(1)

    # Call methods under test
    serialized_file = file.serialize()
    file_str = repr(file)

    # Assertions
    assert serialized_file == {
        'id': 1,
        'file_name': 'file-1.gcode',
        'user_id': 1,
        'user': 'User 1',
        'file_hash': 'hashed-content',
        'created_at': created_time,
    }

    assert file_str == '<File: file-1.gcode, user ID: 1, created at: 2023-12-25 00:00:00>'


def test_tool(mocked_session):
    # Get test file
    tool_repository = ToolRepository(mocked_session)
    tool = tool_repository.get_tool_by_id(1)

    # Call methods under test
    serialized_tool = tool.serialize()
    tool_str = repr(tool)

    # Assertions
    assert serialized_tool == {
        'id': 1,
        'name': 'tool 1',
        'description': 'It is a tool',
        'added_at': created_time,
    }

    assert tool_str == '<Tool: tool 1, description: It is a tool, added at: 2023-12-25 00:00:00>'


def test_material(mocked_session):
    # Get test file
    material_repository = MaterialRepository(mocked_session)
    material = material_repository.get_material_by_id(1)

    # Call methods under test
    serialized_material = material.serialize()
    material_str = repr(material)

    # Assertions
    assert serialized_material == {
        'id': 1,
        'name': 'material 1',
        'description': 'It is a material',
        'added_at': created_time,
    }

    assert material_str == (
        '<Material: material 1, description: It is a material, added at: 2023-12-25 00:00:00>'
    )


def test_user(mocked_session):
    # Get test file
    user_repository = UserRepository(mocked_session)
    user = user_repository.get_user_by_id(1)

    # Call methods under test
    serialized_user = user.serialize()
    user_str = repr(user)

    # Assertions
    assert serialized_user == {
        'id': 1,
        'name': 'User 1',
        'email': 'test@testing.com',
        'role': 'user',
    }

    assert user_str == '<User: User 1, email: test@testing.com, role: user>'
