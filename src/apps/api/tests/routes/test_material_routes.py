from datetime import datetime

from core.domain.entities import Material


def test_list_materials(client, app_context, user_headers, test_material):
    app_context.material_service.get_all_materials.return_value = [test_material]

    response = client.get("/materials/", headers=user_headers)

    assert response.status_code == 200
    assert response.json()[0]["name"] == test_material.name


def test_create_material(client, app_context, admin_headers):
    material = Material(
        id=5,
        name="New material",
        description="New description",
        added_at=datetime(2000, 1, 1),
    )
    app_context.material_service.create_material.return_value = material

    response = client.post(
        "/materials/",
        headers=admin_headers,
        json={"name": material.name, "description": material.description},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 5
    app_context.material_service.create_material.assert_called_once_with(
        material.name, material.description
    )


def test_delete_material(client, app_context, admin_headers):
    response = client.delete("/materials/5", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"success": "El material fue eliminado con éxito"}
    app_context.material_service.remove_material.assert_called_once_with(5)
