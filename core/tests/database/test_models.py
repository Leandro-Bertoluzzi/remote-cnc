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
    task_str = repr(task)

    # Assertions
    assert task_str == '<Task: Task 1, status: pending_approval, created at: 2023-12-25 00:00:00>'


def test_file(mocked_session):
    # Get test file
    file_repository = FileRepository(mocked_session)
    file = file_repository.get_file_by_id(1)

    # Call methods under test
    file_str = repr(file)

    # Assertions
    assert file_str == '<File: file-1.gcode, user ID: 1, created at: 2023-12-25 00:00:00>'


def test_tool(mocked_session):
    # Get test file
    tool_repository = ToolRepository(mocked_session)
    tool = tool_repository.get_tool_by_id(1)

    # Call methods under test
    tool_str = repr(tool)

    # Assertions
    assert tool_str == '<Tool: tool 1, description: It is a tool, added at: 2023-12-25 00:00:00>'


def test_material(mocked_session):
    # Get test file
    material_repository = MaterialRepository(mocked_session)
    material = material_repository.get_material_by_id(1)

    # Call methods under test
    material_str = repr(material)

    # Assertions
    assert material_str == (
        '<Material: material 1, description: It is a material, added at: 2023-12-25 00:00:00>'
    )


def test_user(mocked_session):
    # Get test file
    user_repository = UserRepository(mocked_session)
    user = user_repository.get_user_by_id(1)

    # Call methods under test
    user_str = repr(user)

    # Assertions
    assert user_str == '<User: User 1, email: test@testing.com, role: user>'
