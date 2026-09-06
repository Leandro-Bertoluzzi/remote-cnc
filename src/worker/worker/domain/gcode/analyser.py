import re
from collections import Counter
from typing import Pattern

# Regular expressions to classify commands
pause_pattern = re.compile(r"^(?:N\d+\s+)?M(0|1|00|01)\s*", re.MULTILINE)
comment_pattern = re.compile(r"(^\(.*\)$)|(^;.*)", re.MULTILINE)

# Regular expressions to extract parts of a command
gcode_pattern = re.compile(r"\bG\d+(?:\.\d+)?\b", re.IGNORECASE)
mcode_pattern = re.compile(r"\bM\d+\b", re.IGNORECASE)
feedrate_pattern = re.compile(r"\bF(\d+(?:\.\d+)?)\b", re.IGNORECASE)
t_pattern = re.compile(r"^(?!;|\().*(T\d+)", re.MULTILINE)


class GcodeAnalyser:
    """Utility class to get values of interest from a gcode file."""

    def __init__(
        self,
        content: str,
        valid_gcodes: list[str],
        valid_mcodes: list[str],
    ):
        self._content = self._strip_surrounding_whitespace(content)
        self._normalized_content = self._normalize_content(content)
        self._valid_gcodes = valid_gcodes
        self._valid_mcodes = valid_mcodes

    def analyse(self):
        # 1. Analyze unprocessed content
        content = self._content

        total_lines = len(content.splitlines())
        comment_count = self._count(comment_pattern, content)

        # 2. Analyze normalized content
        content = self._normalized_content

        pause_count = self._count(pause_pattern, content)
        movement_lines = self._count_movement_lines(content)
        tools = self._find_all_unique(t_pattern, content)
        max_feedrate = self._find_max(feedrate_pattern, content)
        commands_gcode = self._count_all(gcode_pattern, content)
        commands_mcode = self._count_all(mcode_pattern, content)

        unsupported_commands = list(
            filter(lambda x: x not in self._valid_gcodes, commands_gcode.keys())
        ) + list(filter(lambda x: x not in self._valid_mcodes, commands_mcode.keys()))

        return {
            "total_lines": total_lines,
            "pause_count": pause_count,
            "movement_lines": movement_lines,
            "comment_count": comment_count,
            "tools": tools,
            "max_feedrate": max_feedrate,
            "commands_usage": {**commands_gcode, **commands_mcode},
            "unsupported_commands": sorted(unsupported_commands),
        }

    def _strip_surrounding_whitespace(self, text: str):
        """Remove leading and trailing whitespace from each line."""
        return "\n".join(line.strip() for line in text.splitlines())

    def _normalize_content(self, text: str):
        """Remove comments and empty lines, normalize G/M command numbers."""
        lines = []

        for line in text.splitlines():
            # Remove semicolon comments.
            line = line.split(";", 1)[0]

            # Remove parenthesized comments.
            line = re.sub(r"\([^)]*\)", "", line)

            # Remove empty lines and whitespace.
            line = line.strip()
            if not line:
                continue

            # Normalize G and M commands to two-digit command numbers.
            line = re.sub(
                r"\b([GM])(\d+)\b",
                lambda match: f"{match.group(1).upper()}{int(match.group(2)):02d}",
                line,
                flags=re.IGNORECASE,
            )

            lines.append(line)

        return "\n".join(lines)

    def _count_movement_lines(self, text: str) -> int:
        """Count lines that perform movement, including modal moves."""
        movement_commands = {"G00", "G01"}
        current_motion = None
        count = 0

        for line in text.splitlines():
            commands = gcode_pattern.findall(line)
            has_motion_command = False

            for command in commands:
                command = command.upper()

                if command in movement_commands:
                    current_motion = command
                    has_motion_command = True

            # A line containing axis coordinates is a movement when a
            # modal movement command is currently active.
            has_coordinates = bool(
                re.search(
                    r"\b[XYZIJKABC]\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)\b",
                    line,
                    re.IGNORECASE,
                )
            )

            if has_motion_command or (current_motion and has_coordinates):
                count += 1

        return count

    # UTILITIES

    def _count(self, regex: Pattern, text: str) -> int:
        return len(regex.findall(text))

    def _count_all(self, regex: Pattern, text: str) -> dict[str, int]:
        return dict(Counter(regex.findall(text)))

    def _find_all_unique(self, regex: Pattern, text: str) -> list[str]:
        matches = regex.findall(text)
        if not matches:
            return []
        list_set = list(set(matches))
        list_set.sort()
        return list_set

    def _find_max(self, regex: Pattern, text: str) -> float:
        matches = regex.findall(text)
        if not matches:
            return 0
        return max(float(x) for x in matches)
