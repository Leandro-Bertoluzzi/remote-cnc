from core.database.base import Base
from core.database.models import Tool
from tests.conftest import engine, TestingSession


# Example tools
test_tool1 = Tool("Tool 1", "A very useful tool")
test_tool2 = Tool("Tool 2", "A not so useful tool")


class TestToolRoutes:
    def setup_class(self):
        # Creates tables in the test database
        Base.metadata.create_all(bind=engine)

        # Seeds the database with test data
        with TestingSession() as session:
            session.add(test_tool1)
            session.add(test_tool2)
            session.commit()

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_get_tools(self, client):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Query endpoint under test
        response = client.get("/tools/", headers=headers)

        # Assertions
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json() == [
            {
                "name": "Tool 1",
                "description": "A very useful tool"
            },
            {
                "name": "Tool 2",
                "description": "A not so useful tool"
            }
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
            'routes.toolRoutes.ToolRepository.create_tool',
            side_effect=Exception('There was an error')
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
        assert response.json() == {"success": "The tool was successfully updated"}

    def test_update_tool_error(self, client, mocker):
        data = {"name": "Updated tool", "description": "An updated tool"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.toolRoutes.ToolRepository.update_tool',
            side_effect=Exception('There was an error')
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
        assert response.json() == {"success": "The tool was successfully removed"}

    def test_remove_tool_error(self, client, mocker):
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock DB method to simulate exception
        mocker.patch(
            'routes.toolRoutes.ToolRepository.remove_tool',
            side_effect=Exception('There was an error')
        )

        # Query endpoint under test
        response = client.delete("/tools/2", headers=headers)

        # Assertions
        assert response.status_code == 400
        assert response.json()["detail"] == "There was an error"
