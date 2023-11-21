import os
import pytest
from database.base import Base
from datetime import datetime

# Set environment variables for tests

os.environ['FILES_FOLDER'] = 'files_folder'
os.environ['SERIAL_PORT'] = 'COMx'


# Settings for mocking SQLAlchemy
@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return Base


@pytest.fixture(scope="function")
def sqlalchemy_mock_config():
    return [
        ("users", [
            {
                "id": 1,
                "name": "User 1",
                "email": "test@testing.com",
                "password": "testpassword",
                "role": "user"
            },
            {
                "id": 2,
                "name": "User 2",
                "email": "test2@testing.com",
                "password": "testpassword2",
                "role": "admin"
            }
        ]),
        ("tools", [
            {
                "id": 1,
                "name": "tool 1",
                "description": "It is a tool",
                "added_at": datetime.now()
            },
            {
                "id": 2,
                "name": "tool 2",
                "description": "It is also a tool",
                "added_at": datetime.now()
            }
        ]),
        ("materials", [
            {
                "id": 1,
                "name": "material 1",
                "description": "It is a material",
                "added_at": datetime.now()
            },
            {
                "id": 2,
                "name": "material 2",
                "description": "It is also a material",
                "added_at": datetime.now()
            }
        ]),
        ("files", [
            {
                "id": 1,
                "user_id": 1,
                "file_name": "file-1.gcode",
                "file_path": "path/to/files/file-1.gcode",
                "created_at": datetime.now()
            },
            {
                "id": 2,
                "user_id": 1,
                "file_name": "file-2.gcode",
                "file_path": "path/to/files/file-2.gcode",
                "created_at": datetime.now()
            }
        ]),
        ("tasks", [
            {
                "id": 1,
                "name": "Task 1",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": None,
                "status": "pending_approval",
                "priority": 0,
                "note": "This is a note",
                "cancellation_reason": None,
                "created_at": datetime.now(),
                "status_updated_at": datetime.now()
            },
            {
                "id": 2,
                "name": "Task 2",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": 1,
                "status": "on_hold",
                "priority": 2,
                "note": "This is a note",
                "cancellation_reason": None,
                "created_at": datetime.now(),
                "status_updated_at": datetime.now()
            },
            {
                "id": 3,
                "name": "Task 3",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": 1,
                "status": "finished",
                "priority": 0,
                "note": "This is a note",
                "cancellation_reason": None,
                "created_at": datetime.now(),
                "status_updated_at": datetime.now()
            },
            {
                "id": 4,
                "name": "Task 4",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": None,
                "status": "cancelled",
                "priority": 0,
                "note": "This is a note",
                "cancellation_reason": "It was necessary",
                "created_at": datetime.now(),
                "status_updated_at": datetime.now()
            },
        ])
    ]
