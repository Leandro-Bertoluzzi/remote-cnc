import pytest
from worker.domain.gcode.analyser import GcodeAnalyser


def analyse(gcode: str) -> dict:
    return GcodeAnalyser(
        content=gcode,
        valid_gcodes=["G00", "G01", "G17", "G20", "G54", "G90", "G94"],
        valid_mcodes=["M00", "M03", "M30"],
    ).analyse()


class TestTotalLines:
    def test_total_lines_is_correct(self):
        gcode = """G00 X0 Y0
        G01 X10 Y10
        G00 X20 Y20"""

        report = analyse(gcode)

        assert report["total_lines"] == 3


class TestCountPauses:
    def test_pause_count_is_correct(self):
        gcode = """
        G00 X0 Y0
        M00
        G01 X10 Y10
        M03
        G00 X20 Y20
        M30
        """

        report = analyse(gcode)

        assert report["pause_count"] == 2


class TestMovementLines:
    def test_movement_lines_are_counted(self):
        gcode = """
        G00 X0 Y0
        G01 X10 Y10
        G00 X20 Y20
        G01 X30 Y30
        """

        report = analyse(gcode)

        assert report["movement_lines"] == 4

    def test_modal_moves_are_counted(self):
        gcode = """
        G00 X0 Y0
        X1 Y1
        X2 Y2
        G01 X10 Y10
        X20 Y20
        """

        report = analyse(gcode)

        assert report["movement_lines"] == 5

    def test_coordinate_only_line_without_active_motion_is_not_a_movement(self):
        gcode = """
        G17
        X0 Y0
        G00 X1 Y1
        X2 Y2
        """

        report = analyse(gcode)

        assert report["movement_lines"] == 2


class TestComments:
    def test_comments_are_counted(self):
        gcode = """
        ; This is a comment
        G01 X10 Y10
        (This is a parenthesized comment)
        G00 X0 Y0
        """

        report = analyse(gcode)

        assert report["comment_count"] == 2

    def test_line_comments_are_counted_but_inline_comments_are_ignored(self):
        gcode = """
        ; This is a comment
        G01 X10 Y10 ; This is another comment
        (This is a parenthesized comment)
        G00 X0 Y0 (This is another parenthesized comment)
        """

        report = analyse(gcode)

        assert report["comment_count"] == 2

    def test_commands_inside_comments_are_ignored(self):
        gcode = """
        G01 X10 Y10 ; G88 M88
        G00 X0 Y0
        """

        report = analyse(gcode)

        assert report["comment_count"] == 0
        assert report["commands_usage"] == {
            "G01": 1,
            "G00": 1,
        }
        assert "G99" not in report["commands_usage"]
        assert "G88" not in report["commands_usage"]
        assert "G77" not in report["commands_usage"]


class TestTools:
    def test_tools_are_found(self):
        gcode = """
        T1 M06
        G00 X0 Y0
        T2 M06
        G01 X10 Y10
        T3 M06
        G00 X20 Y20
        """

        report = analyse(gcode)

        assert report["tools"] == ["T1", "T2", "T3"]


class TestMaxFeedrate:
    def test_max_feedrate_is_found(self):
        gcode = """
        G01 X10 F5
        G01 X20 F10
        G01 X30 F7
        G01 X40 F3
        """

        report = analyse(gcode)

        assert report["max_feedrate"] == 10

    def test_decimal_feedrates_are_supported(self):
        gcode = """
        G01 X10 F5
        G01 X20 F5.5
        G01 X30 F0.25
        G01 X40 F12.75
        """

        report = analyse(gcode)

        assert report["max_feedrate"] == pytest.approx(12.75)


class TestCommandsUsage:
    def test_commands_are_counted(self):
        gcode = """
        G00 X0 Y0
        G01 X10 Y10
        G00 X20 Y20
        G01 X30 Y30
        M00
        M03
        M30
        """

        report = analyse(gcode)

        assert report["commands_usage"] == {
            "G00": 2,
            "G01": 2,
            "M00": 1,
            "M03": 1,
            "M30": 1,
        }

    def test_commands_on_same_line_are_all_counted(self):
        gcode = "G17 G20 G90 G94 G54"

        report = analyse(gcode)

        assert report["commands_usage"] == {
            "G17": 1,
            "G20": 1,
            "G90": 1,
            "G94": 1,
            "G54": 1,
        }

    def test_mcode_on_same_line_are_all_counted(self):
        gcode = "M00 M03 M30"

        report = analyse(gcode)

        assert report["commands_usage"] == {
            "M00": 1,
            "M03": 1,
            "M30": 1,
        }


class TestUnsupportedCommands:
    def test_unsupported_commands_are_reported(self):
        gcode = """
        G00 X0 Y0
        G01 X10 Y10
        G99 X20 Y20
        M88
        G77 X30 Y30
        """

        report = analyse(gcode)

        assert report["unsupported_commands"] == ["G77", "G99", "M88"]


class TestCommandNormalization:
    def test_gcode_leading_zeroes_are_normalized(self):
        gcode = """
        G0 X0 Y0
        G00 X1 Y1
        G1 X2 Y2
        G01 X3 Y3
        """

        report = analyse(gcode)

        assert report["commands_usage"]["G00"] == 2
        assert report["commands_usage"]["G01"] == 2
        assert "G0" not in report["commands_usage"]
        assert "G1" not in report["commands_usage"]

    def test_mcode_leading_zeroes_are_normalized(self):
        gcode = """
        M0
        M00
        M3
        M03
        M30
        """

        report = analyse(gcode)

        assert report["commands_usage"] == {
            "M00": 2,
            "M03": 2,
            "M30": 1,
        }


class TestAnalyserReport:
    def test_example_gcode(self):
        gcode = """G17 G20 G90 G94 G54
        G0 Z0.25
        X-0.5 Y0.
        Z0.1
        G01 Z0. F5.
        G01 X20 Y20
        G01 Z0.1 F5.
        G00 X0. Y0. Z0.25"""

        report = analyse(gcode)

        assert report["total_lines"] == 8
        assert report["pause_count"] == 0
        assert report["comment_count"] == 0
        assert report["max_feedrate"] == pytest.approx(5)
        assert report["commands_usage"] == {
            "G17": 1,
            "G20": 1,
            "G90": 1,
            "G94": 1,
            "G54": 1,
            "G00": 2,
            "G01": 3,
        }
        assert report["movement_lines"] == 7
        assert report["unsupported_commands"] == []

    def test_example_gcode_case_insensitive(self):
        gcode = """g17 g20 g90 g94 g54
        g0 z0.25
        x-0.5 y0.
        z0.1
        g01 z0. f5.
        g01 x20 y20
        g01 z0.1 f5.
        g00 x0. y0. z0.25"""

        report = analyse(gcode)

        assert report["total_lines"] == 8
        assert report["pause_count"] == 0
        assert report["comment_count"] == 0
        assert report["max_feedrate"] == pytest.approx(5)
        assert report["commands_usage"] == {
            "G17": 1,
            "G20": 1,
            "G90": 1,
            "G94": 1,
            "G54": 1,
            "G00": 2,
            "G01": 3,
        }
        assert report["movement_lines"] == 7
        assert report["unsupported_commands"] == []

    def test_complex_example_gcode(self):
        gcode = """G17 G20 G90 G94 G54
        G0 Z0.25
        X-0.5 Y0.
        Z0.1
        G01 Z0. F5.
        G01 X20 Y20
        G01 Z0.1 F5.
        G00 X0. Y0. Z0.25
        ; This is a comment
        (This is a parenthesized comment)
        G99
        M88"""

        report = analyse(gcode)

        assert report["total_lines"] == 12
        assert report["pause_count"] == 0
        assert report["comment_count"] == 2
        assert report["max_feedrate"] == pytest.approx(5)
        assert report["commands_usage"] == {
            "G17": 1,
            "G20": 1,
            "G90": 1,
            "G94": 1,
            "G54": 1,
            "G00": 2,
            "G01": 3,
            "G99": 1,
            "M88": 1,
        }
        assert report["movement_lines"] == 7
        assert report["unsupported_commands"] == ["G99", "M88"]
