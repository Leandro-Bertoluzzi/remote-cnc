import math
import re
from typing import Literal, Optional, TypedDict

# Types definition
Offset = TypedDict("Offset", {"x": float, "y": float, "z": float})
Coordinate = TypedDict("Coordinate", {"x": float, "y": float, "z": float, "F": float})


class GcodeParser:
    def __init__(self):
        self.model = GcodeModel(self)

    def parseFile(self, path: str):
        with open(path, "r") as f:
            # init line counter
            self.lineNb = 0

            for line in f:
                # inc line counter
                self.lineNb += 1
                # remove trailing linefeed
                self.line = line.rstrip()

                self.parseLine()

        self.model.postProcess()
        return self.model

    def parseLine(self):
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
            if hasattr(self, "parse_" + code):
                getattr(self, "parse_" + code)(args)
            else:
                self.warn(f"Unknown code '{code}'")

    def parseArgs(self, args: Optional[str]):
        dic = {}
        if args:
            bits = args.split()
            for bit in bits:
                identifier = bit[0].lower()
                try:
                    coord = float(bit[1:])
                except ValueError:
                    coord = 1
                dic[identifier] = coord
        return dic

    def parse_G00(self, args):
        # G0: Rapid move
        self.model.do_G0_G1(self.parseArgs(args), "G0")

    def parse_G0(self, args):
        # G0: Rapid move
        self.model.do_G0_G1(self.parseArgs(args), "G0")

    def parse_G01(self, args):
        # G1: Controlled move
        self.model.do_G0_G1(self.parseArgs(args), "G1")

    def parse_G1(self, args):
        # G1: Controlled move
        self.model.do_G0_G1(self.parseArgs(args), "G1")

    def parse_G20(self, args):
        # G20: Set Units to Inches
        self.error("Unsupported & incompatible: G20: Set Units to Inches")

    def parse_G21(self, args):
        # G21: Set Units to Millimeters
        # Default, nothing to do
        pass

    def parse_G28(self, args):
        # G28: Move to Origin
        self.model.do_G28(self.parseArgs(args))

    def parse_G90(self, args):
        # G90: Set to Absolute Positioning
        self.model.setRelative(False)

    def parse_G91(self, args):
        # G91: Set to Relative Positioning
        self.model.setRelative(True)

    def parse_G92(self, args):
        # G92: Set Position
        self.model.do_G92(self.parseArgs(args))

    def warn(self, msg: str):
        print(f"[WARN] Line {self.lineNb}: {msg} (Text:'{self.line}')")

    def error(self, msg: str):
        raise Exception(f"[ERROR] Line {self.lineNb}: {msg} (Text:'{self.line}')")


class BBox(object):
    def __init__(self, coords):
        self.xmin = self.xmax = coords["x"]
        self.ymin = self.ymax = coords["y"]
        self.zmin = self.zmax = coords["z"]

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

    def extend(self, coords):
        self.xmin = min(self.xmin, coords["x"])
        self.xmax = max(self.xmax, coords["x"])
        self.ymin = min(self.ymin, coords["y"])
        self.ymax = max(self.ymax, coords["y"])
        self.zmin = min(self.zmin, coords["z"])
        self.zmax = max(self.zmax, coords["z"])


class GcodeModel:
    def __init__(self, parser: GcodeParser):
        # save parser for messages
        self.parser = parser
        # latest coordinates & extrusion relative to offset, feedrate
        self.relative: Coordinate = {"x": 0.0, "y": 0.0, "z": 0.0, "F": 0.0}
        # offsets for relative coordinates and position reset (G92)
        self.offset: Offset = {"x": 0.0, "y": 0.0, "z": 0.0}
        # if true, args for move (G1) are given relatively (default: absolute)
        self.isRelative = False
        # the segments
        self.segments: list[Segment] = []
        self.distance = 0
        self.bbox: Optional[BBox] = None

    def do_G0_G1(self, args: dict, type: Literal["G0", "G1"]):
        # G0/G1: Rapid/Controlled move
        # clone previous coords
        coords: Coordinate = dict(self.relative)
        # update changed coords
        for axis in args.keys():
            if axis in coords:
                if self.isRelative:
                    coords[axis] += args[axis]
                else:
                    coords[axis] = args[axis]
            else:
                self.warn(f"Unknown axis '{axis}'")
        # build segment
        absolute: Coordinate = {
            "x": self.offset["x"] + coords["x"],
            "y": self.offset["y"] + coords["y"],
            "z": self.offset["z"] + coords["z"],
            "F": coords["F"],  # no feedrate offset
        }

        seg = Segment(type, absolute, self.parser.lineNb, self.parser.line)
        self.addSegment(seg)

        # update model coords
        self.relative = coords

    def do_G28(self, args):
        # G28: Move to Origin
        self.warn("G28 unimplemented")

    def do_G92(self, args: dict):
        # G92: Set Position
        # this changes the current coords, without moving, so do not generate a segment

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
                self.warn(f"Unknown axis '{axis}'")

    def setRelative(self, isRelative):
        self.isRelative = isRelative

    def addSegment(self, segment):
        self.segments.append(segment)

    def warn(self, msg: str):
        self.parser.warn(msg)

    def error(self, msg: str):
        self.parser.error(msg)

    def calcMetrics(self):
        # init distance
        self.distance = 0

        # extender helper
        def extend(bbox: Optional[BBox], coords):
            if bbox is None:
                return BBox(coords)
            else:
                bbox.extend(coords)
                return bbox

        # start model at 0
        coords = {"x": 0.0, "y": 0.0, "z": 0.0, "F": 0.0, "E": 0.0, "EE": 0.0}

        # init model bbox
        self.bbox = extend(self.bbox, coords)

        # for all segments
        for seg in self.segments:
            # calc xyz distance
            d = (seg.coords["x"] - coords["x"]) ** 2
            d += (seg.coords["y"] - coords["y"]) ** 2
            d += (seg.coords["z"] - coords["z"]) ** 2
            seg.distance = math.sqrt(d)

            # execute segment
            coords = seg.coords

            # include end point
            extend(self.bbox, coords)

            # accumulate total metrics
            self.distance += seg.distance

    def postProcess(self):
        self.calcMetrics()

    def __str__(self):
        return (
            f"<GcodeModel: len(segments)={len(self.segments)}, "
            f"distance={self.distance}, "
            f"bbox={self.bbox}, "
        )


class Segment:
    def __init__(self, type: str, coords: list[Coordinate], lineNb: int, line: str):
        self.type = type
        self.coords = coords
        self.lineNb = lineNb
        self.line = line
        self.distance = None

    def __str__(self):
        return (
            f"<Segment: type={self.type}, "
            f"<Coords: type={self.coords}, "
            f"lineNb={self.lineNb}, "
            f"line={self.line}, "
            f"distance={self.distance}, "
        )
