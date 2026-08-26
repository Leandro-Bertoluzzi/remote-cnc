from pathlib import Path

import pytest
from worker.domain.gcode.parser import GcodeParser, MovementType, Polyline


def parse_gcode(tmp_path: Path, content: str):
    path = tmp_path / "test.gcode"
    path.write_text(content.strip() + "\n")
    return GcodeParser().parse_file(path)


def points(polyline: Polyline):
    return [(v.x, v.y, v.z) for v in polyline.vertices]


class TestEmptyFile:
    def test_empty_file_has_no_geometry(self, tmp_path):
        model = parse_gcode(tmp_path, "")
        assert model.polylines == []
        assert model.distance == 0.0
        assert model.bbox is None


class TestFirstMovement:
    def test_first_movement_stores_initial_vertex(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10 Y20 Z5")
        assert len(model.polylines) == 1
        p = model.polylines[0]
        assert p.type is MovementType.MACHINING
        assert points(p) == [(0.0, 0.0, 0.0), (10.0, 20.0, 5.0)]


class TestMovementTypes:
    def test_g0_creates_travel_polyline(self, tmp_path):
        model = parse_gcode(tmp_path, "G0 X10 Y20 Z5")
        assert len(model.polylines) == 1
        assert model.polylines[0].type is MovementType.TRAVEL
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 20.0, 5.0)]

    def test_g00_and_g01_create_expected_types(self, tmp_path):
        model = parse_gcode(tmp_path, "G00 X10\nG01 X20")
        assert [p.type for p in model.polylines] == [MovementType.TRAVEL, MovementType.MACHINING]
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
        assert points(model.polylines[1]) == [(10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]

    def test_same_type_moves_stay_in_one_polyline(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nG1 X20\nG1 X20 Y10")
        assert len(model.polylines) == 1
        assert points(model.polylines[0]) == [
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (20.0, 0.0, 0.0),
            (20.0, 10.0, 0.0),
        ]

    def test_movement_type_change_creates_new_polyline(self, tmp_path):
        model = parse_gcode(tmp_path, "G0 X10\nG0 X20\nG1 X30\nG1 X40")
        assert len(model.polylines) == 2
        assert model.polylines[0].type is MovementType.TRAVEL
        assert model.polylines[1].type is MovementType.MACHINING
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
        assert points(model.polylines[1]) == [(20.0, 0.0, 0.0), (30.0, 0.0, 0.0), (40.0, 0.0, 0.0)]


class TestModalMoves:
    def test_modal_move_reuses_last_movement_command(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nX20\nY30")
        assert len(model.polylines) == 1
        assert points(model.polylines[0]) == [
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (20.0, 0.0, 0.0),
            (20.0, 30.0, 0.0),
        ]

    def test_modal_g0_remains_travel(self, tmp_path):
        model = parse_gcode(tmp_path, "G0 X10\nX20\nY30")
        assert model.polylines[0].type is MovementType.TRAVEL
        assert points(model.polylines[0]) == [
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (20.0, 0.0, 0.0),
            (20.0, 30.0, 0.0),
        ]


class TestPositioningMode:
    def test_absolute_positioning_is_default(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10 Y20\nG1 X30 Y40")
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 20.0, 0.0), (30.0, 40.0, 0.0)]

    def test_relative_positioning_accumulates_coordinates(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10 Y20\nG91\nG1 X5 Y-10\nG1 X10")
        assert points(model.polylines[0]) == [
            (0.0, 0.0, 0.0),
            (10.0, 20.0, 0.0),
            (15.0, 10.0, 0.0),
            (25.0, 10.0, 0.0),
        ]

    def test_switching_back_to_absolute_positioning(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nG91\nG1 X5\nG90\nG1 X100")
        assert points(model.polylines[0]) == [
            (0.0, 0.0, 0.0),
            (10.0, 0.0, 0.0),
            (15.0, 0.0, 0.0),
            (100.0, 0.0, 0.0),
        ]


class TestComments:
    def test_comments_are_ignored(self, tmp_path):
        model = parse_gcode(tmp_path, "; comment\nG1 X10 (comment)\nG1 X20 ; comment")
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]


class TestBlankLines:
    def test_blank_lines_do_not_break_polyline(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\n\nG1 X20")
        assert len(model.polylines) == 1
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]


class TestDistance:
    def test_total_distance_is_calculated_from_vertices(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X3\nG1 X3 Y4")
        assert model.distance == pytest.approx(7.0)

    def test_distance_with_multiple_polylines(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nG0 X100\nG1 X110")
        assert model.distance == pytest.approx(110.0)

    def test_distance_with_relative_moves(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nG91\nG1 X3 Y4\nG90\nG1 X20")
        assert model.distance == pytest.approx(22.0)


class TestBoundingBox:
    def test_bounding_box_contains_all_vertices(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10 Y20 Z30\nG0 X-5 Y40 Z-10")
        assert model.bbox is not None
        assert model.bbox.xmin == pytest.approx(-5)
        assert model.bbox.xmax == pytest.approx(10)
        assert model.bbox.ymin == pytest.approx(0)
        assert model.bbox.ymax == pytest.approx(40)
        assert model.bbox.zmin == pytest.approx(-10)
        assert model.bbox.zmax == pytest.approx(30)


class TestUnsupportedCodes:
    def test_g20_is_rejected_as_unsupported(self, tmp_path):
        with pytest.raises(Exception, match="G20"):
            parse_gcode(tmp_path, "G20")

    def test_g28_is_rejected_as_unsupported(self, tmp_path):
        with pytest.raises(Exception, match="G28"):
            parse_gcode(tmp_path, "G28")

    def test_unknown_code_is_only_warned(self, tmp_path, capsys):
        model = parse_gcode(tmp_path, "G1 X10\nG999 X20\nG1 X30")
        captured = capsys.readouterr()
        assert "Unknown code 'G999'" in captured.out
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (30.0, 0.0, 0.0)]


class TestNonMovementCommands:
    def test_non_movement_commands_do_not_create_geometry(self, tmp_path):
        model = parse_gcode(tmp_path, "G17\nG21\nG1 X10\nM30\nG1 X20")
        assert len(model.polylines) == 1
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]

    def test_g92_does_not_create_vertex_or_polyline(self, tmp_path):
        model = parse_gcode(tmp_path, "G1 X10\nG92 X0\nG1 X10")
        assert len(model.polylines) == 1
        assert points(model.polylines[0]) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
