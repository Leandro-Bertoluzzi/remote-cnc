import math
import re
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise
from typing import Literal, TypedDict

# Types definition
Offset = TypedDict("Offset", {"x": float, "y": float, "z": float})
Coordinate = TypedDict("Coordinate", {"x": float, "y": float, "z": float, "f": float})


# Constants
_MODAL_MOVE_CODES = {"G0", "G00", "G1", "G01", "G2", "G02", "G3", "G03"}
_AXIS_LETTERS = set("xyzijkfXYZIJKF")


# Custom exception classes
class GcodeModelError(Exception):
    """Base class for G-code model errors."""

    pass


class UnknownAxisError(GcodeModelError):
    """Raised when an unknown axis letter is encountered in a G-code command."""

    def __init__(self, axis: str):
        super().__init__(f"Unknown axis '{axis}'")


class GcodeParser:
    def __init__(self):
        self.model = GcodeModel(self)
        self.last_move_code: str | None = None

    # -----------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------

    def parse_file(self, path: str):
        with open(path, "r") as f:
            # init line counter
            self.line_number = 0

            for line in f:
                # inc line counter
                self.line_number += 1
                # remove trailing linefeed
                self.line = line.rstrip()

                self._parse_line()

        self.model.post_process()
        return self.model

    # -----------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------

    def _parse_line(self):
        # strip comments:
        # first handle round brackets
        command = re.sub(r"\([^)]*\)", "", self.line)
        # then semicolons
        idx = command.find(";")
        if idx >= 0:
            command = command[0:idx].strip()
        # detect unterminated round bracket comments, just in case
        idx = command.find("(")
        if idx >= 0:
            self.warn("Stripping unterminated round-bracket comment")
            command = command[0:idx].strip()

        # TODO strip logical line number & checksum

        # code is first word, then args
        comm = command.split(None, 1)
        code = comm[0] if (len(comm) > 0) else None
        args = comm[1] if (len(comm) > 1) else None

        if code:
            # Modal: line starts with an axis letter — re-use last movement command
            if code[0] in _AXIS_LETTERS and self.last_move_code is not None:
                getattr(self, "_parse_" + self.last_move_code)(command)
                return

            if hasattr(self, "_parse_" + code):
                getattr(self, "_parse_" + code)(args)
                if code in _MODAL_MOVE_CODES:
                    self.last_move_code = code
            else:
                self.warn(f"Unknown code '{code}'")

    def _parse_args(self, args: str | None) -> dict[str, float]:
        if not args:
            return {}

        dic = {}
        bits = args.split()
        for bit in bits:
            identifier = bit[0].lower()
            try:
                coord = float(bit[1:])
            except ValueError:
                coord = 1
            dic[identifier] = coord
        return dic

    def _parse_G00(self, args):
        # G0: Rapid move
        self._parse_G0(args)

    def _parse_G0(self, args):
        # G0: Rapid move
        try:
            self.model.do_G0_G1(self._parse_args(args), "G0")
        except UnknownAxisError as e:
            self.warn(str(e))

    def _parse_G01(self, args):
        # G1: Controlled move
        self._parse_G1(args)

    def _parse_G1(self, args):
        # G1: Controlled move
        try:
            self.model.do_G0_G1(self._parse_args(args), "G1")
        except UnknownAxisError as e:
            self.warn(str(e))

    def _parse_G17(self, args):
        # G17: Select XY plane
        # Default, nothing to do
        pass

    def _parse_G20(self, args):
        # G20: Set Units to Inches
        self.error("Unsupported & incompatible: G20: Set Units to Inches")

    def _parse_G21(self, args):
        # G21: Set Units to Millimeters
        # Default, nothing to do
        pass

    def _parse_G28(self, args):
        self.error("Unsupported & incompatible: G28: Move to Origin")

    def _parse_G90(self, args):
        # G90: Set to Absolute Positioning
        self.model.set_relative(False)

    def _parse_G91(self, args):
        # G91: Set to Relative Positioning
        self.model.set_relative(True)

    def _parse_G92(self, args):
        # G92: Set Position
        try:
            self.model.do_G92(self._parse_args(args))
        except UnknownAxisError as e:
            self.error(str(e))

    def _parse_M30(self, args):
        # M30: Program Stop and Rewind
        pass

    def warn(self, msg: str):
        print(f"[WARN] Line {self.line_number}: {msg} (Text:'{self.line}')")

    def error(self, msg: str):
        raise Exception(f"[ERROR] Line {self.line_number}: {msg} (Text:'{self.line}')")


@dataclass(slots=True)
class Vertex:
    """A physical position reached by the toolhead."""

    x: float
    y: float
    z: float

    def __str__(self):
        return f"<Vertex: (x={self.x}, y={self.y}, z={self.z})>"


class MovementType(Enum):
    TRAVEL = "travel"
    MACHINING = "machining"


@dataclass(slots=True)
class Polyline:
    """
    A continuous toolpath. Consecutive vertices describe the trajectory of the toolhead.

    `type` describes how the trajectory should be interpreted:
    - "TRAVEL": the toolhead is moving without cutting or extruding
    - "MACHINING": the toolhead is cutting or extruding
    """

    type: MovementType
    vertices: list[Vertex]

    def __str__(self):
        return f"<Polyline: type={self.type} ({len(self.vertices)} vertices)>"


class BBox:
    """Bounding box of a G-code model."""

    def __init__(self, coords: Vertex):
        self.xmin = self.xmax = coords.x
        self.ymin = self.ymax = coords.y
        self.zmin = self.zmax = coords.z

    def dx(self):
        return self.xmax - self.xmin

    def dy(self):
        return self.ymax - self.ymin

    def dz(self):
        return self.zmax - self.zmin

    def cx(self):
        return (self.xmax + self.xmin) / 2

    def cy(self):
        return (self.ymax + self.ymin) / 2

    def cz(self):
        return (self.zmax + self.zmin) / 2

    def extend(self, coords: Vertex):
        self.xmin = min(self.xmin, coords.x)
        self.xmax = max(self.xmax, coords.x)
        self.ymin = min(self.ymin, coords.y)
        self.ymax = max(self.ymax, coords.y)
        self.zmin = min(self.zmin, coords.z)
        self.zmax = max(self.zmax, coords.z)


class GcodeModel:
    def __init__(self, parser: GcodeParser):
        # save parser for messages
        self.parser = parser

        self._reset()

    def _reset(self):
        # Latest coordinates & extrusion relative to offset, feedrate
        self.relative: Coordinate = {"x": 0.0, "y": 0.0, "z": 0.0, "f": 0.0}
        # Offsets for relative coordinates and position reset (G92)
        self.offset: Offset = {"x": 0.0, "y": 0.0, "z": 0.0}
        # If true, args for move (G1) are given relatively (default: absolute)
        self.is_relative = False
        # The trajectories of the toolhead
        self.polylines: list[Polyline] = []
        # Metrics
        self.distance = 0
        self.bbox: BBox | None = None
        # The polyline currently being constructed while parsing.
        self._current_polyline: Polyline | None = None

    def do_G0_G1(self, args: dict, type: Literal["G0", "G1"]):
        """
        Process a physical G0/G1 movement.

        Raises:
            UnknownAxisError: If an unknown axis letter is encountered in the G-code command.
        """

        # --------------------------------------------------------------
        # Calculate the current physical position.
        #
        # `relative` is the logical G-code position.
        # `offset` contains the correction introduced by G92.
        # --------------------------------------------------------------

        start = {
            "x": self.offset["x"] + self.relative["x"],
            "y": self.offset["y"] + self.relative["y"],
            "z": self.offset["z"] + self.relative["z"],
        }

        # --------------------------------------------------------------
        # Clone current logical coordinates.
        # --------------------------------------------------------------

        coords = Coordinate(
            x=self.relative["x"], y=self.relative["y"], z=self.relative["z"], f=self.relative["f"]
        )

        # --------------------------------------------------------------
        # Apply coordinates specified by the movement command.
        # --------------------------------------------------------------

        for axis in args.keys():
            if axis in coords:
                if self.is_relative:
                    coords[axis] += args[axis]
                else:
                    coords[axis] = args[axis]
            else:
                raise UnknownAxisError(axis)

        # --------------------------------------------------------------
        # Convert destination from logical coordinates into physical
        # machine coordinates.
        # --------------------------------------------------------------

        end = {
            "x": self.offset["x"] + coords["x"],
            "y": self.offset["y"] + coords["y"],
            "z": self.offset["z"] + coords["z"],
        }

        # --------------------------------------------------------------
        # G0 = travel movement
        # G1 = machining movement
        # --------------------------------------------------------------

        movement_type = MovementType.TRAVEL if type == "G0" else MovementType.MACHINING

        # --------------------------------------------------------------
        # If this is the first physical movement, add the initial
        # machine position.
        # --------------------------------------------------------------

        if self._current_polyline is None:
            self._add_vertex(
                movement_type,
                Vertex(x=start["x"], y=start["y"], z=start["z"]),
            )

        # --------------------------------------------------------------
        # Add the destination vertex.
        # --------------------------------------------------------------

        self._add_vertex(
            movement_type,
            Vertex(x=end["x"], y=end["y"], z=end["z"]),
        )

        # --------------------------------------------------------------
        # Update logical coordinates only after constructing the vertex.
        # --------------------------------------------------------------

        self.relative = coords

    def do_G92(self, args: dict):
        """
        Process a G92 command to set the current position of the toolhead.
        This changes the current coordinates without moving, so no vertices are added.

        Raises:
            UnknownAxisError: If an unknown axis letter is encountered.
        """

        # no axes mentioned == all axes to 0
        if not len(args.keys()):
            args = {"x": 0.0, "y": 0.0, "z": 0.0, "E": 0.0}
        # update specified axes
        for axis in args.keys():
            if axis in self.offset:
                # transfer value from relative to offset
                self.offset[axis] += self.relative[axis] - args[axis]
                self.relative[axis] = args[axis]
            else:
                raise UnknownAxisError(axis)

    def set_relative(self, is_relative):
        self.is_relative = is_relative

    def _add_vertex(
        self,
        movement_type: MovementType,
        vertex: Vertex,
    ):
        """
        Add a vertex to the current toolpath.
        A new Polyline is created whenever the movement type changes.
        """

        if self._current_polyline is None or self._current_polyline.type != movement_type:
            # Save the last vertex of the previous polyline, if any.
            last_vertex = None
            if self._current_polyline and self._current_polyline.vertices:
                last_vertex = self._current_polyline.vertices[-1]

            # Create a new polyline for the new movement type.
            self._current_polyline = Polyline(
                type=movement_type,
                vertices=[],
            )

            # Add the new polyline to the model.
            self.polylines.append(self._current_polyline)

            # Initialize the new polyline with the last vertex of the previous polyline, if any.
            if last_vertex:
                self._current_polyline.vertices.append(last_vertex)

        self._current_polyline.vertices.append(vertex)

    def calc_metrics(self):
        """Calculate total toolpath distance and bounding box."""

        self.distance = 0.0
        self.bbox = None

        for polyline in self.polylines:
            for vertex in polyline.vertices:
                # Initialize or extend the model bounding box.
                if self.bbox is None:
                    self.bbox = BBox(vertex)
                else:
                    self.bbox.extend(vertex)

            # Calculate distances between consecutive vertices.
            for start, end in pairwise(polyline.vertices):
                dx = end.x - start.x
                dy = end.y - start.y
                dz = end.z - start.z

                self.distance += math.sqrt(dx * dx + dy * dy + dz * dz)

    def post_process(self):
        self.calc_metrics()

    def __str__(self):
        return (
            f"<GcodeModel: {len(self.polylines)} polylines, "
            f"distance={self.distance}, "
            f"bbox={self.bbox}>"
        )
