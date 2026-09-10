import pytest
from core.domain.logs import interpret_log


class TestLogsInterpreter:
    @pytest.mark.parametrize(
        "log,expected_time,expected_level,expected_type,expected_message",
        [
            (
                "[28/02/2024 19:45:55] INFO: [Sent] command: $X",
                "28/02/2024 19:45:55",
                "INFO",
                "Sent",
                "command: $X",
            ),
            (
                "[28/02/2024 19:47:59] INFO: [Parsed] Message type: GrblResultOk",
                "28/02/2024 19:47:59",
                "INFO",
                "Parsed",
                "Message type: GrblResultOk",
            ),
            (
                "[28/02/2024 19:45:55] WARNING: Homing cycle required at startup, handling...",
                "28/02/2024 19:45:55",
                "WARNING",
                None,
                "Homing cycle required at startup, handling...",
            ),
            (
                "[29/02/2024 19:21:33] ERROR: Error: Unsupported command. Description: ...",
                "29/02/2024 19:21:33",
                "ERROR",
                None,
                "Error: Unsupported command. Description: ...",
            ),
            (
                "[05/03/2024 19:09:11] CRITICAL: Failed opening serial port COM5",
                "05/03/2024 19:09:11",
                "CRITICAL",
                None,
                "Failed opening serial port COM5",
            ),
        ],
    )
    def test_interpret_log(
        self, log, expected_time, expected_level, expected_type, expected_message
    ):
        # Call method under test
        result = interpret_log(log)
        assert result is not None
        time, level, msg_type, message = result

        # Assertions
        assert time == expected_time
        assert level == expected_level
        assert msg_type == expected_type
        assert message == expected_message

    def test_interpret_invalid_log(self):
        # Call method under test
        result = interpret_log("invalid log")

        # Assertions
        assert result is None
