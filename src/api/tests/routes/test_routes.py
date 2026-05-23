import hashlib

import pytest  # noqa: F401
from api_db import TestingSession, engine, test_admin, test_user
from core.adapters.database.base import Base
from core.adapters.database.file_repository import FileRepository
from core.adapters.database.material_repository import MaterialRepository
from core.adapters.database.task_repository import TaskRepository
from core.adapters.database.tool_repository import ToolRepository
from core.adapters.database.user_repository import UserRepository
from core.adapters.file_manager import FileManager


class TestRoutes:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            user_repository = UserRepository(session)
            file_repository = FileRepository(session)
            material_repository = MaterialRepository(session)
            tool_repository = ToolRepository(session)
            task_repository = TaskRepository(session)

            created_user = user_repository.create_user(
                test_user.name, test_user.email, "password", test_user.role
            )
            created_admin = user_repository.create_user(
                test_admin.name, test_admin.email, "password", test_admin.role
            )

            file1 = file_repository.create_file(
                created_user.id, "file_1.gcode", hashlib.sha256(b"G54").hexdigest()
            )
            file_repository.create_file(
                created_user.id, "file_2.gcode", hashlib.sha256(b"G55").hexdigest()
            )
            file_repository.create_file(
                created_admin.id, "file_3.gcode", hashlib.sha256(b";empty").hexdigest()
            )

            material1 = material_repository.create_material("Material 1", "A very useful material")
            material_repository.create_material("Material 2", "A not so useful material")

            tool1 = tool_repository.create_tool("Tool 1", "A very useful tool")
            tool_repository.create_tool("Tool 2", "A not so useful tool")

            task_repository.create_task(
                created_user.id, file1.id, tool1.id, material1.id, "Task 1", "A note"
            )
            task2 = task_repository.create_task(
                created_user.id, file1.id, tool1.id, material1.id, "Task 2", "A note"
            )
            task_repository.update_task_status(task2.id, "on_hold", created_admin.id)
            task3 = task_repository.create_task(
                created_admin.id, file1.id, tool1.id, material1.id, "Task 3", "A note"
            )
            task_repository.update_task_status(task3.id, "on_hold", created_admin.id)

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    # --------------------------------------------------------------------- #
    # ------------------------------- USERS ------------------------------- #
    # --------------------------------------------------------------------- #

    def test_user_auth(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/users/auth", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {
            "message": "Successfully authenticated",
            "data": {"id": 1, "name": "User", "email": "user@test.com", "role": "user"},
        }

    def test_login(self, client):
        data = {"email": "admin@test.com", "password": "password"}

        # Query endpoint under test
        response = client.post("/login", json=data)

        # Assertions
        assert response.status_code == 200
        assert response.json()["message"] == "Usuario autenticado con éxito"

    def test_login_invalid_email(self, client):
        data = {"email": "invalid@test.com", "password": "password"}

        # Query endpoint under test
        response = client.post("/login", json=data)

        # Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "No autorizado: Email inválido"

    def test_login_invalid_password(self, client):
        data = {"email": "admin@test.com", "password": "invalid-password"}

        # Query endpoint under test
        response = client.post("/login", json=data)

        # Assertions
        assert response.status_code == 404
        error_msg = response.json()["detail"]
        assert error_msg == "No autorizado: Combinación inválida de email y contraseña"

    def test_login_db_error(self, client, mocker):
        data = {"email": "admin@test.com", "password": "password"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.userRoutes.UserRepository.get_user_by_email",
            side_effect=Exception("There was an error looking for the user"),
        )

        # Query endpoint under test
        response = client.post("/login", json=data)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error looking for the user"

    def test_login_token_error(self, client, mocker):
        data = {"email": "admin@test.com", "password": "password"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.userRoutes.generate_token",
            side_effect=Exception("There was an error generating the token"),
        )

        # Query endpoint under test
        response = client.post("/login", json=data)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error generating the token"

    def test_get_users(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/users/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {"id": 1, "name": "User", "email": "user@test.com", "role": "user"},
            {"id": 2, "name": "Admin", "email": "admin@test.com", "role": "admin"},
        ]

    def test_create_user(self, client):
        data = {
            "name": "testuser",
            "email": "testuser@nofoobar.com",
            "password": "aVerySecureP@ssw0rd",
            "role": "user",
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/users/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "testuser"
        assert response.json()["email"] == "testuser@nofoobar.com"
        assert response.json()["role"] == "user"

    def test_create_user_error(self, client, mocker):
        data = {
            "name": "testuser2",
            "email": "testuser2@nofoobar.com",
            "password": "aVerySecureP@ssw0rd",
            "role": "user",
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.userRoutes.UserRepository.create_user",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.post("/users/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_update_user(self, client):
        data = {"name": "testupdate", "email": "updateduser@nofoobar.com", "role": "user"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/users/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "testupdate"
        assert response.json()["email"] == "updateduser@nofoobar.com"
        assert response.json()["role"] == "user"

    def test_update_user_error(self, client, mocker):
        data = {"name": "testupdate", "email": "updateduser@nofoobar.com", "role": "user"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.userRoutes.UserRepository.update_user",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.put("/users/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_remove_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.delete("/users/3", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "El usuario fue eliminado con éxito"}

    def test_remove_user_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.userRoutes.UserRepository.remove_user",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.delete("/users/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    # --------------------------------------------------------------------- #
    # ------------------------------- FILES ------------------------------- #
    # --------------------------------------------------------------------- #

    def test_get_files_from_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/files/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {"id": 1, "name": "file_1.gcode", "user_id": 1, "created_at": "2000-01-01T00:00:00"},
            {"id": 2, "name": "file_2.gcode", "user_id": 1, "created_at": "2000-01-01T00:00:00"},
        ]

    def test_get_all_files(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/files/all", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json() == [
            {"id": 1, "name": "file_1.gcode", "user_id": 1, "created_at": "2000-01-01T00:00:00"},
            {"id": 2, "name": "file_2.gcode", "user_id": 1, "created_at": "2000-01-01T00:00:00"},
            {"id": 3, "name": "file_3.gcode", "user_id": 2, "created_at": "2000-01-01T00:00:00"},
        ]

    def test_create_file(self, client, mocker):
        files = {"file": ("new_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch.object(FileManager, "upload_file", return_value=3)
        mocker.patch("routes.fileRoutes.generateFileReport.delay")
        mocker.patch("routes.fileRoutes.createThumbnail.delay")

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "new_file.gcode"

    def test_create_file_repeated_name(self, client):
        files = {"file": ("file_1.gcode", b"G55", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == ("Ya existe un archivo con el nombre <<file_1.gcode>>")

    def test_create_file_duplicated_content(self, client):
        files = {"file": ("another_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == ("El archivo <<file_1.gcode>> tiene el mismo contenido")

    def test_create_file_error(self, client, mocker):
        files = {"file": ("another_file.gcode", b"G54 G90", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate exception
        mocker.patch.object(
            FileManager, "upload_file", side_effect=Exception("There was an error saving the file")
        )

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error saving the file"

    def test_update_file(self, client, mocker):
        data = {"file_name": "updated_file.gcode"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch.object(FileManager, "rename_file_by_id")

        # Query endpoint under test
        response = client.put("/files/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "updated_file.gcode"

    def test_update_file_error(self, client, mocker):
        data = {"file_name": "updated_file.gcode"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate exception
        mocker.patch.object(
            FileManager,
            "rename_file_by_id",
            side_effect=Exception("There was an error updating the file"),
        )

        # Query endpoint under test
        response = client.put("/files/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error updating the file"

    def test_remove_file(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch.object(FileManager, "remove_file_by_id")

        # Query endpoint under test
        response = client.delete("/files/4", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "El archivo fue eliminado con éxito"}

    def test_remove_file_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate exception
        mocker.patch.object(
            FileManager,
            "remove_file_by_id",
            side_effect=Exception("There was an error removing the file"),
        )

        # Query endpoint under test
        response = client.delete("/files/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error removing the file"

    # --------------------------------------------------------------------- #
    # ------------------------------- TOOLS ------------------------------- #
    # --------------------------------------------------------------------- #

    def test_get_tools(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "id": 1,
                "name": "Tool 1",
                "description": "A very useful tool",
                "added_at": "2000-01-01T00:00:00",
            },
            {
                "id": 2,
                "name": "Tool 2",
                "description": "A not so useful tool",
                "added_at": "2000-01-01T00:00:00",
            },
        ]

    def test_create_tool(self, client):
        data = {"name": "New tool", "description": "A new tool"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/tools/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "New tool"
        assert response.json()["description"] == "A new tool"

    def test_create_tool_error(self, client, mocker):
        data = {"name": "New tool", "description": "Another new tool"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.toolRoutes.ToolRepository.create_tool",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.post("/tools/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_update_tool(self, client):
        data = {"name": "Updated tool", "description": "An updated tool"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/tools/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "Updated tool"
        assert response.json()["description"] == "An updated tool"

    def test_update_tool_error(self, client, mocker):
        data = {"name": "Updated tool", "description": "An updated tool"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.toolRoutes.ToolRepository.update_tool",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.put("/tools/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_remove_tool(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.delete("/tools/3", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "La herramienta fue eliminada con éxito"}

    def test_remove_tool_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.toolRoutes.ToolRepository.remove_tool",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.delete("/tools/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    # --------------------------------------------------------------------- #
    # ----------------------------- MATERIALS ----------------------------- #
    # --------------------------------------------------------------------- #

    def test_get_materials(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/materials/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "id": 1,
                "name": "Material 1",
                "description": "A very useful material",
                "added_at": "2000-01-01T00:00:00",
            },
            {
                "id": 2,
                "name": "Material 2",
                "description": "A not so useful material",
                "added_at": "2000-01-01T00:00:00",
            },
        ]

    def test_create_material(self, client):
        data = {"name": "New material", "description": "A new material"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/materials/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "New material"
        assert response.json()["description"] == "A new material"

    def test_create_material_error(self, client, mocker):
        data = {"name": "New material", "description": "Another new material"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.materialRoutes.MaterialRepository.create_material",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.post("/materials/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_update_material(self, client):
        data = {"name": "Updated material", "description": "An updated material"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/materials/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "Updated material"
        assert response.json()["description"] == "An updated material"

    def test_update_material_error(self, client, mocker):
        data = {"name": "Updated material", "description": "An updated material"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.materialRoutes.MaterialRepository.update_material",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.put("/materials/3", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_remove_material(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.delete("/materials/3", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "El material fue eliminado con éxito"}

    def test_remove_material_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.materialRoutes.MaterialRepository.remove_material",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.delete("/materials/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    # --------------------------------------------------------------------- #
    # ------------------------------- TASKS ------------------------------- #
    # --------------------------------------------------------------------- #

    def test_get_tasks_from_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/tasks/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "id": 1,
                "name": "Task 1",
                "status": "pending_approval",
                "priority": 0,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
                "admin_id": None,
                "cancellation_reason": None,
                "created_at": "2000-01-01T00:00:00",
            },
            {
                "id": 2,
                "name": "Task 2",
                "status": "on_hold",
                "priority": 1,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
                "admin_id": None,
                "cancellation_reason": None,
                "created_at": "2000-01-01T00:00:00",
            },
        ]

    def test_get_all_tasks(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/tasks/all", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json() == [
            {
                "id": 1,
                "name": "Task 1",
                "status": "pending_approval",
                "priority": 0,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
                "admin_id": None,
                "cancellation_reason": None,
                "created_at": "2000-01-01T00:00:00",
            },
            {
                "id": 3,
                "name": "Task 3",
                "status": "on_hold",
                "priority": 1,
                "user_id": 2,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
                "admin_id": None,
                "cancellation_reason": None,
                "created_at": "2000-01-01T00:00:00",
            },
            {
                "id": 2,
                "name": "Task 2",
                "status": "on_hold",
                "priority": 1,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
                "admin_id": None,
                "cancellation_reason": None,
                "created_at": "2000-01-01T00:00:00",
            },
        ]

    def test_create_task(self, client):
        data = {"file_id": 1, "tool_id": 1, "material_id": 1, "name": "New task", "note": "A note"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/tasks/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "New task"
        assert response.json()["file_id"] == 1
        assert response.json()["tool_id"] == 1
        assert response.json()["material_id"] == 1
        assert response.json()["note"] == "A note"
        assert response.json()["status"] == "pending_validation"

    def test_create_task_error(self, client, mocker):
        data = {"file_id": 1, "tool_id": 1, "material_id": 1, "name": "New task", "note": "A note"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.taskRoutes.TaskRepository.create_task",
            side_effect=Exception("There was an error creating the task in DB"),
        )

        # Query endpoint under test
        response = client.post("/tasks/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "There was an error creating the task in DB"}

    def test_update_task(self, client):
        data = {
            "file_id": 2,
            "tool_id": 2,
            "material_id": 2,
            "name": "Updated task",
            "note": "A new note",
            "priority": 5,
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/tasks/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["name"] == "Updated task"
        assert response.json()["file_id"] == 2
        assert response.json()["tool_id"] == 2
        assert response.json()["material_id"] == 2
        assert response.json()["priority"] == 5
        assert response.json()["note"] == "A note"

    def test_update_task_error(self, client, mocker):
        data = {
            "file_id": 2,
            "tool_id": 2,
            "material_id": 2,
            "name": "Updated task",
            "note": "A new note",
            "priority": 5,
        }
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.taskRoutes.TaskRepository.update_task",
            side_effect=Exception("There was an error updating the task in DB"),
        )

        # Query endpoint under test
        response = client.put("/tasks/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "There was an error updating the task in DB"}

    def test_update_task_status(self, client):
        data = {"status": "cancelled"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/tasks/4/status", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json()["status"] == "on_hold"

    def test_update_task_status_error(self, client, mocker):
        data = {"status": "on_hold"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.taskRoutes.TaskRepository.update_task_status",
            side_effect=Exception("There was an error updating the task in DB"),
        )

        # Query endpoint under test
        response = client.put("/tasks/4/status", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "There was an error updating the task in DB"}

    def test_remove_task(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.delete("/tasks/4", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "La tarea fue eliminada con éxito"}

    def test_remove_task_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.taskRoutes.TaskRepository.remove_task",
            side_effect=Exception("There was an error removing the task from DB"),
        )

        # Query endpoint under test
        response = client.delete("/tasks/3", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json() == {"detail": "There was an error removing the task from DB"}
