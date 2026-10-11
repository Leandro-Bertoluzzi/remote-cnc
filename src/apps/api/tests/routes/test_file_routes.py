def test_list_files_for_user(client, app_context, user_headers, test_file, test_other_file):
    app_context.file_service.get_all_files_from_user.return_value = [test_file, test_other_file]

    response = client.get("/files/", headers=user_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [test_file.id, test_other_file.id]
    app_context.file_service.get_all_files_from_user.assert_called_once_with(1)


def test_upload_file_delegates_to_file_service(client, app_context, user_headers, test_file):
    app_context.file_service.upload_file.return_value = test_file

    response = client.post(
        "/files/",
        headers=user_headers,
        files={"file": ("uploaded.gcode", b"G54", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["id"] == test_file.id
    args = app_context.file_service.upload_file.call_args.args
    assert args[:2] == (1, "uploaded.gcode")


def test_upload_file_missing_filename(client, user_headers):
    response = client.post(
        "/files/",
        headers=user_headers,
        files={"file": ("", b"G54", "text/plain")},
    )

    assert response.status_code == 422
