from pathlib import Path

from core.application.logs_interpreter import LogsInterpreter
from pytest_mock.plugin import MockerFixture


class TestLogsInterpreter:
    def test_interpret_file(self, mocker: MockerFixture):
        # Mock FS methods
        mocker.patch("os.path.exists", return_value=True)

        mocked_file_data = mocker.mock_open(
            read_data=(
                "[28/02/2024 19:45:55] INFO: Started USB connection at port COM5\n"
                "[28/02/2024 19:45:55] WARNING: Handling homing cycle at startup...\n"
                "[28/02/2024 19:45:55] INFO: [Sent] command: $X\n"
                "[28/02/2024 19:45:55] INFO: [Received] GRBL: [MSG:Caution: Unlocked]\n"
                "[28/02/2024 19:45:55] INFO: [Parsed] Message type: GrblMsgFeedback\n"
                "[28/02/2024 19:45:55] INFO: Alarm was successfully disabled\n"
                "invalid line, just ignore\n"
                "[28/02/2024 19:45:55] INFO: [Received] GRBL: ok\n"
                "[28/02/2024 19:45:55] INFO: [Parsed] Message type: GrblResultOk\n"
                "[28/02/2024 19:45:55] INFO: Started execution of file: path/to/file.gcode\n"
                "[28/02/2024 19:45:55] INFO: [Sent] command: G91\n"
                "[28/02/2024 19:45:55] INFO: [Sent] command: G00 X0 Y0 F70\n"
            )
        )
        mocker.patch("builtins.open", mocked_file_data)

        # Call method under test
        result = LogsInterpreter.interpret_file(Path())

        # Assertions
        assert list(result) == [
            ("28/02/2024 19:45:55", "INFO", None, "Started USB connection at port COM5"),
            ("28/02/2024 19:45:55", "WARNING", None, "Handling homing cycle at startup..."),
            ("28/02/2024 19:45:55", "INFO", "Sent", "command: $X"),
            ("28/02/2024 19:45:55", "INFO", "Received", "GRBL: [MSG:Caution: Unlocked]"),
            ("28/02/2024 19:45:55", "INFO", "Parsed", "Message type: GrblMsgFeedback"),
            ("28/02/2024 19:45:55", "INFO", None, "Alarm was successfully disabled"),
            ("28/02/2024 19:45:55", "INFO", "Received", "GRBL: ok"),
            ("28/02/2024 19:45:55", "INFO", "Parsed", "Message type: GrblResultOk"),
            ("28/02/2024 19:45:55", "INFO", None, "Started execution of file: path/to/file.gcode"),
            ("28/02/2024 19:45:55", "INFO", "Sent", "command: G91"),
            ("28/02/2024 19:45:55", "INFO", "Sent", "command: G00 X0 Y0 F70"),
        ]

    def test_interpret_file_non_existing(self, mocker: MockerFixture):
        # Mock FS methods
        mocker.patch("os.path.exists", return_value=False)

        # Call method under test
        result = LogsInterpreter.interpret_file(Path())

        # Assertions
        assert list(result) == []
