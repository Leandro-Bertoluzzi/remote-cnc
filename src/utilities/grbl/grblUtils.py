import re
from utilities.grbl.constants import GRBL_SETTINGS

# Constants
JOG_UNIT_MILIMETERS = 'milimeters'
JOG_UNIT_INCHES = 'inches'
JOG_DISTANCE_ABSOLUTE = 'distance_absolute'
JOG_DISTANCE_INCREMENTAL = 'distance_incremental'

# Regular expressions
grbl_setting_pattern = re.compile(r'^\$(\d+)=(\d+\.?\d*)$')


def build_jog_command(
        x: float,
        y: float,
        z: float,
        feedrate: float, *,
        units=None,
        distance_mode=None,
        machine_coordinates=False
) -> str:
    """
    Builds a 'jog' command from the parameters.

    JOG mode is also called jogging mode.
    In this mode, the CNC machine is used to operate manually.
    """
    jog_command_parts = ["$J="]

    # Build GRBL command
    if machine_coordinates:
        jog_command_parts.append("G53")

    if distance_mode == JOG_DISTANCE_ABSOLUTE:
        jog_command_parts.append("G90")
    elif distance_mode == JOG_DISTANCE_INCREMENTAL:
        jog_command_parts.append("G91")

    if units == JOG_UNIT_INCHES:
        jog_command_parts.append("G20")
    elif units == JOG_UNIT_MILIMETERS:
        jog_command_parts.append("G21")

    if x or distance_mode == JOG_DISTANCE_ABSOLUTE:
        jog_command_parts.append(f"X{x}")
    if y or distance_mode == JOG_DISTANCE_ABSOLUTE:
        jog_command_parts.append(f"Y{y}")
    if z or distance_mode == JOG_DISTANCE_ABSOLUTE:
        jog_command_parts.append(f"Z{z}")
    if feedrate:
        jog_command_parts.append(f"F{feedrate}")

    return " ".join(jog_command_parts)


def is_setting_update_command(command) -> bool:
    """Checks if the command is a GRBL setting.

    For example:
    $23=5
    $27=5.200
    """
    matches = grbl_setting_pattern.search(command)

    if (not matches):
        return False

    parameter = matches.group(1)
    # value = matches.group(2)

    if int(parameter) > 132:
        return False
    return True


def get_grbl_setting(key: str):
    for element in GRBL_SETTINGS:
        if element['setting'] == key:
            return element
    return None
