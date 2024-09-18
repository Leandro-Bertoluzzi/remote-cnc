from gcode.gcodeAnalyser import GcodeAnalyser
import pytest
from pytest_mock.plugin import MockerFixture


class TestGcodeAnalyser:
    @pytest.mark.parametrize("content,expected", [
        (
            """G90
G1 F3000
; feature prime pillar
; tool H0.250 W0.480
G1 Z0.500 F1500
G1 X24.263 Y95.358 F21000
G1 Z0.250 F1500
G1 F3000
G1 X33.783 Y95.358 F1200
G1 X33.783 Y104.878
G1 X24.263 Y104.878
G1 X24.263 Y95.358
G1 F3000
""",
            {
                'total_lines': 13,
                'pause_count': 0,
                'movement_lines': 10,
                'comment_count': 2,
                'tools': [],
                'max_feedrate': 21000,
                'commands_usage': { 'G1': 10, 'G90': 1 },
                'unsupported_commands': []
            }
        ),
        (
            """N30 T02
N40 T15
(N50 G01 X10 F20)
N60 G00 Y20
N70 G00 F5000
N80 M00
N90 G66
""",
            {
                'total_lines': 7,
                'pause_count': 1,
                'movement_lines': 2,
                'comment_count': 1,
                'tools': ['T02', 'T15'],
                'max_feedrate': 5000,
                'commands_usage': { 'G00': 2, 'G66': 1, 'M00': 1 },
                'unsupported_commands': ['G66']
            }
        ),
    ])
    def test_file_sender_start(
        self,
        mocker: MockerFixture,
        content,
        expected
    ):
        analyser = GcodeAnalyser('/path/to/file')

        # Mock FS methods
        mocked_file_data = mocker.mock_open(read_data=content)
        mocker.patch('builtins.open', mocked_file_data)

        # Call method under test
        result = analyser.analyse()

        # Assertions
        assert result == expected
