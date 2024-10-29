import re
from utilities.grbl.constants import GRBL_SETTINGS

# Constants
JOG_UNIT_MILIMETERS = 'milimeters'
JOG_UNIT_INCHES = 'inches'
JOG_DISTANCE_ABSOLUTE = 'distance_absolute'
JOG_DISTANCE_INCREMENTAL = 'distance_incremental'


def build_jog_command(
        x: float,
        y: float,
        z: float,
        feedrate: float, *,
        units=None,
        distance_mode=None,
        machine_coordinates=False
) -> str:
    """Builds a 'jog' command from the parameters.

    JOG mode is also called jogging mode.
    In this mode, the CNC machine is used to operate manually.
    """
    jog_command = "$J="

    # Build GRBL command
    if machine_coordinates:
        jog_command = jog_command + 'G53 '

    if distance_mode == JOG_DISTANCE_ABSOLUTE:
        jog_command = jog_command + 'G90 '
    if distance_mode == JOG_DISTANCE_INCREMENTAL:
        jog_command = jog_command + 'G91 '

    if units == JOG_UNIT_INCHES:
        jog_command = jog_command + 'G20 '
    if units == JOG_UNIT_MILIMETERS:
        jog_command = jog_command + 'G21 '

    x_str = f'X{x} ' if x or distance_mode == JOG_DISTANCE_ABSOLUTE else ''
    y_str = f'Y{y} ' if y or distance_mode == JOG_DISTANCE_ABSOLUTE else ''
    z_str = f'Z{z} ' if z or distance_mode == JOG_DISTANCE_ABSOLUTE else ''
    feedrate_str = f'F{feedrate}' if feedrate else ''
    jog_command = jog_command + x_str + y_str + z_str + feedrate_str
    return jog_command.strip()


def is_setting_update_command(command) -> bool:
    """Checks if the command is a GRBL setting.

    For example:
    $23=5
    $27=5.200
    """
    matches = re.search(r'^\$(\d+)=(\d+\.?\d*)$', command)

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
