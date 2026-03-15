import re
from collections import Counter
from typing import Pattern

from core.utilities.gcode.constants import GCODE_VALID_GCODES, GCODE_VALID_MCODES

# Regular expressions to classify commands
pause_pattern = re.compile(r"^(?:N\d+\s+)?M(0|1|00|01)\s*", re.MULTILINE)
move_pattern = re.compile(r"^(?:N\d+\s+)?G(0|1|00|01)\s*", re.MULTILINE)
comment_pattern = re.compile(r"(^\(.*\)$)|(^;.*)", re.MULTILINE)

# Regular expressions to extract parts of a command (not comments)
gcode_pattern = re.compile(r"^(?!;|\().*(G\d+(?:.\d)?)", re.MULTILINE)
mcode_pattern = re.compile(r"^(?!;|\().*(M\d+)", re.MULTILINE)
feedrate_pattern = re.compile(r"^(?!;|\().*F(\d+)", re.MULTILINE)
t_pattern = re.compile(r"^(?!;|\().*(T\d+)", re.MULTILINE)


class GcodeAnalyser:
    """Utility class to get values of interest from a gcode file."""

    def __init__(self, file_path: str):
        # Attributes definition
        self.file_path = file_path

    def analyse(self):
        # Initialize values of interest
        total_lines = 0
        comment_count = 0
        movement_lines = 0
        pause_count = 0
        tools = []
        max_feedrate = 0
        commands_gcode = {}
        commands_mcode = {}
        unsupported_commands = []

        # Static analysis
        with open(self.file_path, "r") as gcode:
            content = gcode.read()

            total_lines = len(content.splitlines())

            pause_count = self._count(pause_pattern, content)
            movement_lines = self._count(move_pattern, content)
            comment_count = self._count(comment_pattern, content)

            tools = self._find_all_unique(t_pattern, content)

            max_feedrate = self._find_max(feedrate_pattern, content)

            commands_gcode = self._count_all(gcode_pattern, content)
            commands_mcode = self._count_all(mcode_pattern, content)

            unsupported_commands = list(
                filter(lambda x: x not in GCODE_VALID_GCODES, commands_gcode.keys())
            ) + list(filter(lambda x: x not in GCODE_VALID_MCODES, commands_mcode.keys()))

        return {
            "total_lines": total_lines,
            "pause_count": pause_count,
            "movement_lines": movement_lines,
            "comment_count": comment_count,
            "tools": tools,
            "max_feedrate": max_feedrate,
            "commands_usage": {**commands_gcode, **commands_mcode},
            "unsupported_commands": unsupported_commands,
        }

    # UTILITIES

    def _count(self, regex: Pattern, text: str):
        matches = regex.findall(text)
        return len(matches)

    def _count_all(self, regex: Pattern, text: str):
        matches = regex.findall(text)
        return dict(Counter(matches))

    def _find_all_unique(self, regex: Pattern, text: str):
        matches = regex.findall(text)
        if not matches:
            return []

        list_set = list(set(matches))
        list_set.sort()
        return list_set

    def _find_max(self, regex: Pattern, text: str):
        matches = regex.findall(text)
        if not matches:
            return 0

        values = [int(x) for x in matches]
        return max(values)
