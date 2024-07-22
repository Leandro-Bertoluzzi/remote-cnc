from core.utils.serial import SerialService


class TestCncRoutes:
    def test_send_code(self, client, mocker):
        data = {"command": "G54"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock G-code validation
        mock_validator = mocker.patch('routes.cncRoutes.validateGcodeBlock')

        # Mock serial port operation
        mock_connect_port = mocker.patch.object(SerialService, 'startConnection', return_value='ok')
        mock_send_command = mocker.patch.object(SerialService, 'streamBlock', return_value='ok')
        mock_disconnect_port = mocker.patch.object(SerialService, 'stopConnection')

        # Query route under test
        response = client.post("/cnc/command", json=data, headers=headers)

        # Assertions
        assert mock_validator.call_count == 1
        assert mock_connect_port.call_count == 1
        assert mock_send_command.call_count == 1
        assert mock_disconnect_port.call_count == 1
        assert response.status_code == 200
        assert response.json() == {"result": "ok"}

    def test_send_code_validation_error(self, client, mocker):
        data = {"command": "G54"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock G-code validation to simulate exception
        mock_validator = mocker.patch(
            'routes.cncRoutes.validateGcodeBlock',
            side_effect=Exception('There was an error validating the code')
        )

        # Mock serial port operation
        mock_connect_port = mocker.patch.object(SerialService, 'startConnection')

        # Query route under test
        response = client.post("/cnc/command", json=data, headers=headers)

        # Assertions
        assert mock_validator.call_count == 1
        assert mock_connect_port.call_count == 0
        assert response.status_code == 400
        assert response.json() == {"detail": "There was an error validating the code"}

    def test_send_code_serial_error(self, client, mocker):
        data = {"command": "G54"}
        headers = {"Authorization": "Bearer a-valid-token"}

        # Mock G-code validation
        mock_validator = mocker.patch('routes.cncRoutes.validateGcodeBlock')

        # Mock serial port operation to simulate exception
        mocker.patch.object(
            SerialService,
            'startConnection',
            side_effect=Exception('There was an error connecting to device')
        )

        # Query route under test
        response = client.post("/cnc/command", json=data, headers=headers)

        # Assertions
        assert mock_validator.call_count == 1
        assert response.status_code == 400
        assert response.json() == {
            "detail": "Could not start connection. Check if port is already used."
        }
