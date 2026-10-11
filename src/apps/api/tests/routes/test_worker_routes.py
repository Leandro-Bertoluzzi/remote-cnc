def test_worker_status(client, user_headers, app_context):
    response = client.get("/worker/check/on", headers=user_headers)

    assert response.status_code == 200
    assert response.json() == {"is_on": True}


def test_worker_execution_dispatches_task(client, admin_headers, app_context):
    response = client.post("/worker/task/42", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"worker_task_id": "worker-task-1"}
    assert app_context.worker.dispatched_tasks == [42]


def test_worker_execution_rejects_busy_device(client, admin_headers, app_context):
    app_context.worker.running = True

    response = client.post("/worker/task/42", headers=admin_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Equipo ocupado: Hay una tarea en progreso"
    assert app_context.worker.dispatched_tasks == []


def test_worker_availability(client, user_headers, app_context):
    response = client.get("/worker/check/available", headers=user_headers)

    assert response.status_code == 200
    assert response.json() == {"enabled": True, "running": False, "available": True}
