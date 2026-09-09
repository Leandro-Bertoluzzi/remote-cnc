from core.adapters.database.base import Base
from core.adapters.database.file_repository import FileRepository
from core.adapters.database.material_repository import MaterialRepository
from core.adapters.database.task_repository import TaskRepository
from core.adapters.database.tool_repository import ToolRepository
from core.adapters.database.user_repository import UserRepository

from apps.api.tests.conftest import TestingSession, engine, test_admin, test_user


class TestTaskRoutes:
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

            file = file_repository.create_file(created_user.id, "file_1.gcode", "hash-1")
            material = material_repository.create_material("Material 1", "A very useful material")
            tool = tool_repository.create_tool("Tool 1", "A very useful tool")

            task_repository.create_task(
                created_user.id, file.id, tool.id, material.id, "Task 1", "A note"
            )
            task2 = task_repository.create_task(
                created_user.id, file.id, tool.id, material.id, "Task 2", "A note"
            )
            task_repository.update_task_status(task2.id, "on_hold", created_admin.id)
            task3 = task_repository.create_task(
                created_admin.id, file.id, tool.id, material.id, "Task 3", "A note"
            )
            task_repository.update_task_status(task3.id, "on_hold", created_admin.id)

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_get_tasks_from_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/tasks/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "name": "Task 1",
                "status": "pending_approval",
                "priority": 0,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
            },
            {
                "name": "Task 2",
                "status": "on_hold",
                "priority": 1,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
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
                "name": "Task 1",
                "status": "pending_approval",
                "priority": 0,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
            },
            {
                "name": "Task 2",
                "status": "on_hold",
                "priority": 1,
                "user_id": 1,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
            },
            {
                "name": "Task 3",
                "status": "on_hold",
                "priority": 1,
                "user_id": 2,
                "file_id": 1,
                "tool_id": 1,
                "material_id": 1,
                "note": "A note",
            },
        ]

    def test_create_task(self, client):
        data = {"file_id": 1, "tool_id": 1, "material_id": 1, "name": "New task", "note": "A note"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.post("/tasks/", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The task was successfully created"}

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
        assert response.json() == {"success": "The task was successfully updated"}

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
        data = {"status": "on_hold"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.put("/tasks/4/status", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The task status was successfully updated"}

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
        assert response.json() == {"success": "The task was successfully removed"}

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
