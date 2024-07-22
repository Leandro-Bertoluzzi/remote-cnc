import re
from typing import BinaryIO

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

# Define regular expressions to match G-code commands
g_pattern = re.compile(r'^(?:N\d+\s+)?G\d+\s*')
m_pattern = re.compile(r'^(?:N\d+\s+)?M\d+\s*')
comment_pattern = re.compile(r'(^\(.*\)$)|(^;.*)')
xyz_pattern = re.compile(r'^(?:N\d+\s+)?[XYZ][-+]?\d+(\.\d*)?(?:\s|$)')
empty_pattern = re.compile(r'^\s*$')

# Define regular expressions to extract parts of the command
gcode_pattern = re.compile(r'G\d+(.\d)?')
mcode_pattern = re.compile(r'M\d+')


def validateGcodeFile(file: BinaryIO):
    fileContent = file.readlines()

    # Split the file content in lines and strip all EOL characters for consistency
    gcode = [line.decode().strip() for line in fileContent]

    # Parse each line
    for line in gcode:
        validateGcodeLine(line)
    return


def validateGcodeBlock(code: str):
    # Parse each line
    for line in code.splitlines():
        # Strip all EOL characters for consistency
        validateGcodeLine(line.strip())
    return


def validateGcodeLine(line: str):
    if g_pattern.match(line):
        # Validate motion command
        validate_motion_command(line)
    elif m_pattern.match(line):
        # Validate miscellaneous command
        validate_misc_command(line)
    elif comment_pattern.match(line):
        # It is a comment, do nothing
        print('Comment detected: ', line)
    elif xyz_pattern.match(line):
        # Validate motion commands omitting the G-code
        validate_xyz_command(line)
    elif empty_pattern.match(line):
        # It is an empty line, do nothing
        print('Empty line detected')
    else:
        # Unknown command, syntax error
        raise Exception(f'Syntax error in line: << {line} >>')
    return


def validate_motion_command(command: str):
    # Validate motion command parameters
    # For example:
    # Check that X, Y, and Z values are within a valid range
    # Check that feed rate is non-negative
    print('G-command detected: ', command)

    codes = gcode_pattern.findall(command)

    for code in codes:
        if code not in VALID_GCODES:
            raise Exception(f'Unsupported G code: << {code} >>')
    return


def validate_misc_command(command: str):
    # Validate miscellaneous command parameters
    # For example:
    # Check that tool number is valid
    # Check that spindle speed is non-negative
    print('M-command detected: ', command)

    code = mcode_pattern.match(command).group(0)

    if code not in VALID_MCODES:
        raise Exception(f'Unsupported M code: << {code} >>')
    return


def validate_xyz_command(command: str):
    # Validate modal motion command parameters, when omitting the G-code
    # For example:
    # Check that a modal motion command is actually being executed
    # Check that X, Y, and Z values are within a valid range
    # Check that feed rate is non-negative
    print('Continued modal G-command detected: ', command)
    return
