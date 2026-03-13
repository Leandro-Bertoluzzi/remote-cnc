from collections import Counter
import re
from typing import Pattern

'''
List of Supported G-Codes in Grbl v1.1:
  - Non-Modal Commands: G4, G10L2, G10L20, G28, G30, G28.1, G30.1, G53, G92, G92.1
  - Motion Modes: G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
  - Feed Rate Modes: G93, G94
  - Unit Modes: G20, G21
  - Distance Modes: G90, G91
  - Arc IJK Distance Modes: G91.1
  - Plane Select Modes: G17, G18, G19
  - Tool Length Offset Modes: G43.1, G49
  - Cutter Compensation Modes: G40
  - Coordinate System Modes: G54, G55, G56, G57, G58, G59
  - Control Modes: G61
  - Program Flow: M0, M1, M2, M30*
  - Coolant Control: M7*, M8, M9
  - Spindle Control: M3, M4, M5
  - Valid Non-Command Words: F, I, J, K, L, N, P, R, S, T, X, Y, Z
  (*) Commands not enabled by default in config.h
'''

# Define valid command codes
VALID_GCODES = [
    'G0', 'G1', 'G2', 'G3', 'G38.2', 'G38.3', 'G38.4', 'G38.5', 'G80',    # Motion Modes
    'G4', 'G10', 'G28', 'G30', 'G28.1', 'G30.1', 'G53', 'G92', 'G92.1',   # Non-Modal Commands
    'G93', 'G94',                                                         # Feed Rate Modes
    'G20', 'G21',                                                         # Unit modes
    'G90', 'G91',                                                         # Distance modes
    'G91.1',                                                        # Arc IJK Distance Modes
    'G17', 'G18', 'G19',                                            # Plane Select Modes
    'G43.1', 'G49',                                                 # Tool Length Offset Modes
    'G40',                                                          # Cutter Compensation Modes
    'G54', 'G55', 'G56', 'G57', 'G58', 'G59',                       # Coordinate System Modes
    'G61',                                                          # Control Modes
    'G00', 'G01', 'G02', 'G03', 'G04',                              # Alternative syntax for codes
]

VALID_MCODES = [
    'M0', 'M1', 'M2', 'M00', 'M01', 'M02', 'M30',  # Program Flow
    'M7', 'M8', 'M9', 'M07', 'M08', 'M09',         # Coolant Control
    'M3', 'M4', 'M5', 'M03', 'M04', 'M05',         # Spindle Control
]

# Regular expressions to classify commands
pause_pattern = r'^(?:N\d+\s+)?M(0|1|00|01)\s*'
move_pattern = r'^(?:N\d+\s+)?G(0|1|00|01)\s*'
comment_pattern = r'(^\(.*\)$)|(^;.*)'

# Regular expressions to extract parts of a command (not comments)
gcode_pattern = r'^(?!;|\().*(G\d+(?:.\d)?)'
mcode_pattern = r'^(?!;|\().*(M\d+)'
feedrate_pattern = r'^(?!;|\().*F(\d+)'
t_pattern = r'^(?!;|\().*(T\d+)'


class GcodeAnalyser:
    """Utility class to get values of interest from a gcode file.
    """

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
        with open(self.file_path, 'r') as gcode:
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
                filter(lambda x: x not in VALID_GCODES, commands_gcode.keys())
            ) + list(
                filter(lambda x: x not in VALID_MCODES, commands_mcode.keys())
            )

        return {
            'total_lines': total_lines,
            'pause_count': pause_count,
            'movement_lines': movement_lines,
            'comment_count': comment_count,
            'tools': tools,
            'max_feedrate': max_feedrate,
            'commands_usage': {**commands_gcode, **commands_mcode},
            'unsupported_commands': unsupported_commands
        }

    # UTILITIES

    def _count(self, regex: Pattern, text: str):
        matches = re.findall(regex, text, re.MULTILINE)
        return len(matches)

    def _count_all(self, regex: Pattern, text: str):
        matches = re.findall(regex, text, re.MULTILINE)
        return dict(Counter(matches))

    def _find_all_unique(self, regex: Pattern, text: str):
        matches = re.findall(regex, text, re.MULTILINE)
        if not matches:
            return []

        list_set = list(set(matches))
        list_set.sort()
        return list_set

    def _find_max(self, regex: Pattern, text: str):
        matches = re.findall(regex, text, re.MULTILINE)
        if not matches:
            return 0

        values = [int(x) for x in matches]
        return max(values)
