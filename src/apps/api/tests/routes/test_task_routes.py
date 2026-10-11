from core.domain.exceptions import InvalidTaskStatus


def test_list_tasks_for_user(client, app_context, user_headers, test_task):
    app_context.task_service.get_all_tasks_from_user.return_value = [test_task]

    response = client.get("/tasks/", headers=user_headers)

    assert response.status_code == 200
    assert response.json()[0]["id"] == test_task.id
    app_context.task_service.get_all_tasks_from_user.assert_called_once_with(1, "all")


def test_create_task(client, app_context, user_headers, test_task):
    app_context.task_service.create_task.return_value = test_task
    payload = {
        "file_id": test_task.file_id,
        "tool_id": test_task.tool_id,
        "material_id": test_task.material_id,
        "name": test_task.name,
        "note": test_task.note,
    }

    response = client.post("/tasks/", headers=user_headers, json=payload)

    assert response.status_code == 200
    assert response.json()["id"] == test_task.id
    app_context.task_service.create_task.assert_called_once_with(
        1,
        payload["file_id"],
        payload["tool_id"],
        payload["material_id"],
        payload["name"],
        payload["note"],
    )


def test_update_task_status_invalid_transition(client, app_context, user_headers):
    app_context.task_service.update_task_status.side_effect = InvalidTaskStatus(
        "invalid transition"
    )

    response = client.put(
        "/tasks/1/status",
        headers=user_headers,
        json={"status": "finished", "cancellation_reason": ""},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid transition"
