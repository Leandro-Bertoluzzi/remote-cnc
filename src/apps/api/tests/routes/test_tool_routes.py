from datetime import datetime

from core.domain.entities import Tool


def test_list_tools(client, app_context, user_headers, test_tool):
    app_context.tool_service.get_all_tools.return_value = [test_tool]

    response = client.get("/tools/", headers=user_headers)

    assert response.status_code == 200
    assert response.json()[0]["name"] == test_tool.name


def test_create_tool(client, app_context, admin_headers):
    tool = Tool(
        id=5, name="New tool", description="New description", added_at=datetime(2000, 1, 1)
    )
    app_context.tool_service.create_tool.return_value = tool

    response = client.post(
        "/tools/",
        headers=admin_headers,
        json={"name": tool.name, "description": tool.description},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 5
    app_context.tool_service.create_tool.assert_called_once_with(tool.name, tool.description)


def test_delete_tool(client, app_context, admin_headers):
    response = client.delete("/tools/5", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"success": "La herramienta fue eliminada con éxito"}
    app_context.tool_service.remove_tool.assert_called_once_with(5)
