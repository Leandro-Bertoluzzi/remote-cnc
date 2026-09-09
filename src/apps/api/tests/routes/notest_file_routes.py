from core.adapters.database.base import Base
from core.adapters.database.file_repository import FileRepository
from core.adapters.database.user_repository import UserRepository

from apps.api.tests.conftest import TestingSession, engine, test_admin, test_user


class TestFileRoutes:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            user_repository = UserRepository(session)
            file_repository = FileRepository(session)

            created_user = user_repository.create_user(
                test_user.name, test_user.email, "password", test_user.role
            )
            created_admin = user_repository.create_user(
                test_admin.name, test_admin.email, "password", test_admin.role
            )

            file_repository.create_file(created_user.id, "file_1.gcode", "hash-1")
            file_repository.create_file(created_user.id, "file_2.gcode", "hash-2")
            file_repository.create_file(created_admin.id, "file_3.gcode", "hash-3")

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_get_files_from_user(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/files/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {"file_name": "file_1.gcode", "user_id": 1},
            {"file_name": "file_2.gcode", "user_id": 1},
        ]

    def test_get_all_files(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/files/all", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 3
        assert response.json() == [
            {"file_name": "file_1.gcode", "user_id": 1},
            {"file_name": "file_2.gcode", "user_id": 1},
            {"file_name": "file_3.gcode", "user_id": 2},
        ]

    def test_create_file(self, client, mocker):
        files = {"file": ("new_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock file validation
        mocker.patch("routes.fileRoutes.validateGcodeFile")

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.saveFile", return_value="generated_file_name.gcode")

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The file was successfully uploaded"}

    def test_create_file_validation_error(self, client, mocker):
        files = {"file": ("new_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock file validation to simulate exception
        mocker.patch(
            "routes.fileRoutes.validateGcodeFile",
            side_effect=Exception("There was an error validating the file"),
        )

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error validating the file"

    def test_create_file_fs_error(self, client, mocker):
        files = {"file": ("new_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock file validation
        mocker.patch("routes.fileRoutes.validateGcodeFile")

        # Mock FS method to simulate exception
        mocker.patch(
            "routes.fileRoutes.saveFile",
            side_effect=Exception("There was an error saving the file in the FS"),
        )

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error saving the file in the FS"

    def test_create_file_db_error(self, client, mocker):
        files = {"file": ("new_file.gcode", b"G54", "text/plain")}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock file validation
        mocker.patch("routes.fileRoutes.validateGcodeFile")

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.saveFile", return_value="generated_file_name.gcode")

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.fileRoutes.FileRepository.create_file",
            side_effect=Exception("There was an error saving the file in DB"),
        )

        # Query endpoint under test
        response = client.post("/files/", files=files, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error saving the file in DB"

    def test_update_file(self, client, mocker):
        data = {"file_name": "updated_file.gcode"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.renameFile", return_value="generated_file_name.gcode")

        # Query endpoint under test
        response = client.put("/files/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The file name was successfully updated"}

    def test_update_file_fs_error(self, client, mocker):
        data = {"file_name": "updated_file.gcode"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate exception
        mocker.patch(
            "routes.fileRoutes.renameFile",
            side_effect=Exception("There was an error updating the file in the FS"),
        )

        # Query endpoint under test
        response = client.put("/files/4", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error updating the file in the FS"

    def test_update_file_db_error(self, client, mocker):
        data = {"file_name": "updated_file.gcode"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.renameFile", return_value="generated_file_name.gcode")

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.fileRoutes.FileRepository.update_file",
            side_effect=Exception("There was an error updating the file in DB"),
        )

        # Query endpoint under test
        response = client.put("/files/1", json=data, headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error updating the file in DB"

    def test_remove_file(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.deleteFile")

        # Query endpoint under test
        response = client.delete("/files/4", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"success": "The file was successfully removed"}

    def test_remove_file_fs_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate exception
        mocker.patch("routes.fileRoutes.deleteFile", side_effect=Exception("There was an error"))

        # Query endpoint under test
        response = client.delete("/files/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"

    def test_remove_file_db_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock FS method to simulate file operation
        mocker.patch("routes.fileRoutes.deleteFile")

        # Mock DB method to simulate exception
        mocker.patch(
            "routes.fileRoutes.FileRepository.remove_file",
            side_effect=Exception("There was an error"),
        )

        # Query endpoint under test
        response = client.delete("/files/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"
