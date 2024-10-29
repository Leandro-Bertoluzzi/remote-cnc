from database.base import Base
from database.models import Material
from conftest import engine, TestingSession


# Example materials
test_material1 = Material("Material 1", "A very useful material")
test_material2 = Material("Material 2", "A not so useful material")


class TestMaterialRoutes:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            session.add(test_material1)
            session.add(test_material2)
            session.commit()

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_get_materials(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/materials/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "name": "Material 1",
                "description": "A very useful material"
            },
            {
                "name": "Material 2",
                "description": "A not so useful material"
            }
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
            'routes.materialRoutes.MaterialRepository.create_material',
            side_effect=Exception('There was an error')
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
        assert response.json() == {"success": "The material was successfully updated"}

    def test_update_material_error(self, client, mocker):
        data = {"name": "Updated material", "description": "An updated material"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.materialRoutes.MaterialRepository.update_material',
            side_effect=Exception('There was an error')
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
        assert response.json() == {"success": "The material was successfully removed"}

    def test_remove_material_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.materialRoutes.MaterialRepository.remove_material',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.delete("/materials/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"
