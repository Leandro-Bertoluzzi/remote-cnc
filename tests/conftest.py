import pytest
from database.base import Base
from datetime import datetime


# Constants
created_time = datetime(2023, 12, 25, 0, 0, 0)


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
                "added_at": created_time
            },
            {
                "id": 2,
                "name": "tool 2",
                "description": "It is also a tool",
                "added_at": created_time
            }
        ]),
        ("materials", [
            {
                "id": 1,
                "name": "material 1",
                "description": "It is a material",
                "added_at": created_time
            },
            {
                "id": 2,
                "name": "material 2",
                "description": "It is also a material",
                "added_at": created_time
            }
        ]),
        ("files", [
            {
                "id": 1,
                "user_id": 1,
                "file_name": "file-1.gcode",
                "file_hash": "hashed-content",
                "created_at": created_time
            },
            {
                "id": 2,
                "user_id": 2,
                "file_name": "file-2.gcode",
                "file_hash": "hashed-content-2",
                "created_at": created_time
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
                "created_at": created_time,
                "status_updated_at": created_time
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
                "created_at": created_time,
                "status_updated_at": created_time
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
                "created_at": created_time,
                "status_updated_at": created_time
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
                "created_at": created_time,
                "status_updated_at": created_time
            },
            {
                "id": 5,
                "name": "Task 5",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": 1,
                "status": "in_progress",
                "priority": 3,
                "note": "This is a note",
                "cancellation_reason": None,
                "created_at": created_time,
                "status_updated_at": created_time
            },
            {
                "id": 6,
                "name": "Task 6",
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "admin_id": 1,
                "status": "failed",
                "priority": 0,
                "note": "This is a note",
                "cancellation_reason": None,
                "created_at": created_time,
                "status_updated_at": created_time
            },
        ])
    ]
