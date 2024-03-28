from pathlib import Path
import pytest
from pytest_mock.plugin import MockerFixture
from utils.logs import LogsInterpreter, LogFileWatcher


class TestLogsInterpreter:
    @pytest.mark.parametrize(
            'log,expected_time,expected_level,expected_type,expected_message',
            [
                (
                    '[28/02/2024 19:45:55] INFO: [Sent] command: $X',
                    '28/02/2024 19:45:55',
                    'INFO',
                    'Sent',
                    'command: $X'
                ),
                (
                    '[28/02/2024 19:47:59] INFO: [Parsed] Message type: GrblResultOk',
                    '28/02/2024 19:47:59',
                    'INFO',
                    'Parsed',
                    'Message type: GrblResultOk'
                ),
                (
                    '[28/02/2024 19:45:55] WARNING: Homing cycle required at startup, handling...',
                    '28/02/2024 19:45:55',
                    'WARNING',
                    None,
                    'Homing cycle required at startup, handling...'
                ),
                (
                    '[29/02/2024 19:21:33] ERROR: Error: Unsupported command. Description: ...',
                    '29/02/2024 19:21:33',
                    'ERROR',
                    None,
                    'Error: Unsupported command. Description: ...'
                ),
                (
                    '[05/03/2024 19:09:11] CRITICAL: Failed opening serial port COM5',
                    '05/03/2024 19:09:11',
                    'CRITICAL',
                    None,
                    'Failed opening serial port COM5'
                ),
            ]
        )
    def test_interpret_log(
        self,
        log,
        expected_time,
        expected_level,
        expected_type,
        expected_message
    ):
        # Call method under test
        time, level, msg_type, message = LogsInterpreter.interpret_log(log)

        # Assertions
        assert time == expected_time
        assert level == expected_level
        assert msg_type == expected_type
        assert message == expected_message

    def test_interpret_invalid_log(self):
        # Call method under test
        result = LogsInterpreter.interpret_log('invalid log')

        # Assertions
        assert result is None

    def test_interpret_file(self, mocker: MockerFixture):
        # Mock FS methods
        mocked_file_data = mocker.mock_open(
            read_data=(
                '[28/02/2024 19:45:55] INFO: Started USB connection at port COM5\n'
                '[28/02/2024 19:45:55] WARNING: Handling homing cycle at startup...\n'
                '[28/02/2024 19:45:55] INFO: [Sent] command: $X\n'
                '[28/02/2024 19:45:55] INFO: [Received] GRBL: [MSG:Caution: Unlocked]\n'
                '[28/02/2024 19:45:55] INFO: [Parsed] Message type: GrblMsgFeedback\n'
                '[28/02/2024 19:45:55] INFO: Alarm was successfully disabled\n'
                'invalid line, just ignore\n'
                '[28/02/2024 19:45:55] INFO: [Received] GRBL: ok\n'
                '[28/02/2024 19:45:55] INFO: [Parsed] Message type: GrblResultOk\n'
                '[28/02/2024 19:45:55] INFO: Started execution of file: path/to/file.gcode\n'
                '[28/02/2024 19:45:55] INFO: [Sent] command: G91\n'
                '[28/02/2024 19:45:55] INFO: [Sent] command: G00 X0 Y0 F70\n'
            )
        )
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        result = LogsInterpreter.interpret_file(Path())

        # Assertions
        assert result == [
            ('28/02/2024 19:45:55', 'INFO', None, 'Started USB connection at port COM5'),
            ('28/02/2024 19:45:55', 'WARNING', None, 'Handling homing cycle at startup...'),
            ('28/02/2024 19:45:55', 'INFO', 'Sent', 'command: $X'),
            ('28/02/2024 19:45:55', 'INFO', 'Received', 'GRBL: [MSG:Caution: Unlocked]'),
            ('28/02/2024 19:45:55', 'INFO', 'Parsed', 'Message type: GrblMsgFeedback'),
            ('28/02/2024 19:45:55', 'INFO', None, 'Alarm was successfully disabled'),
            ('28/02/2024 19:45:55', 'INFO', 'Received', 'GRBL: ok'),
            ('28/02/2024 19:45:55', 'INFO', 'Parsed', 'Message type: GrblResultOk'),
            ('28/02/2024 19:45:55', 'INFO', None, 'Started execution of file: path/to/file.gcode'),
            ('28/02/2024 19:45:55', 'INFO', 'Sent', 'command: G91'),
            ('28/02/2024 19:45:55', 'INFO', 'Sent', 'command: G00 X0 Y0 F70')
        ]


class TestLogFileWatcher:
    def test_watch_log_file(self, mocker: MockerFixture):
        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data='')
        mocked_file = mocker.patch('builtins.open', mocked_file_data)

        mocker.patch.object(mocked_file(), 'readline', side_effect=[
            '[28/02/2024 19:45:55] INFO: Interesting information',
            '[28/02/2024 19:45:55] WARNING: A warning...',
            'Not a log message, just ignore',
            '[28/02/2024 19:45:55] INFO: [Sent] command: $X'
        ])

        # Instantiate class under test
        watcher = LogFileWatcher(Path)
        assert watcher.is_watching is False

        # Call method under test
        logs = watcher.watch()

        # Assertions
        assert next(logs) == ('28/02/2024 19:45:55', 'INFO', None, 'Interesting information')
        assert watcher.is_watching is True
        assert next(logs) == ('28/02/2024 19:45:55', 'WARNING', None, 'A warning...')
        assert next(logs) == ('28/02/2024 19:45:55', 'INFO', 'Sent', 'command: $X')

        # Stop watching file
        watcher.stop_watching()
        assert watcher.is_watching is False
