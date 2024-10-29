from utilities.grbl.constants import GrblActiveState
from utilities.grbl.types import Coordinates, GrblControllerState, GrblError, PositionType
from enum import Enum
from typing import Optional

# Flags


class GrblStatusFlag(Enum):
    CONNECTED = 'connected' # Machine is connected
    STOP = 'stop'           # Request to stop current run
    FINISHED = 'finished'   # Notification of program end (M2/M30)
    PAUSED = 'paused'       # Machine is on Hold
    ALARM = 'alarm'         # Display alarm message

# Constants


DEFAULT_GRBL_CONTROLLER_STATE = {
    'status': {
        'activeState': '',
        'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'ov': [],
        'subState': None,
        'wco': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'pinstate': None,
        'buffer': None,
        'line': None,
        'accessoryState': None
    },
    'parserstate': {
        'modal': {
            'motion': 'G0',
            'wcs': 'G54',
            'plane': 'G17',
            'units': 'G21',
            'distance': 'G90',
            'feedrate': 'G94',
            'program': 'M0',
            'spindle': 'M5',
            'coolant': 'M9'
        },
        'tool': 0,
        'feedrate': 0.0,
        'spindle': 0.0
    }
}


class GrblStatus:
    _state: GrblControllerState = DEFAULT_GRBL_CONTROLLER_STATE

    def __init__(self):
        # Errors management
        self._error_line: Optional[str] = None
        self._error_data: Optional[GrblError] = None

        # Flags
        self._flags = {s.value: False for s in GrblStatusFlag}

    # SETTERS

    def set_flag(self, key: str, value: bool):
        self._flags[key] = value

    def set_active_state(self, state: str):
        self._state['status']['activeState'] = state

    def update_status(self, status: dict[str, str]):
        self._state['status'].update(status)

    def update_parser_state(self, parser_state: dict[str, str]):
        self._state['parserstate'].update(parser_state)

    def set_tool(self, tool_index: int):
        """Sets the GRBL device's current tool."""
        self._state['parserstate']['tool'] = tool_index

    def set_error(self, line: str, data: GrblError):
        self._error_line = line
        self._error_data = data

    def clear_error(self) -> bool:
        """Resets the error-related fields."""
        if self.is_alarm():
            return False

        self._error_line = None
        self._error_data = None
        return True

    # GETTERS

    def get_flag(self, key: str):
        return self._flags.get(key, False)

    def get_position(self, pos_type: PositionType) -> Coordinates:
        """Returns either the machine or work position.

        Example: { 'x': 0.000, 'y': 0.000, 'z': 0.000 }
        """
        return self._state['status'][pos_type]

    def get_modal(self) -> dict[str, str]:
        """Returns the GRBL device's current modal state.

        Example: {
            'motion': 'G0',
            'wcs': 'G54',
            'plane': 'G17',
            'units': 'G21',
            'distance': 'G90',
            'feedrate': 'G94',
            'program': 'M0',
            'spindle': 'M5',
            'coolant': 'M9'
        }

        Fields description:
            - 'motion': G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
            - 'wcs': G54, G55, G56, G57, G58, G59
            - 'plane': G17: xy-plane, G18: xz-plane, G19: yz-plane
            - 'units': G20: Inches, G21: Millimeters
            - 'distance': G90: Absolute, G91: Relative
            - 'feedrate': G93: Inverse time mode, G94: Units per minute
            - 'program': M0, M1, M2, M30
            - 'spindle': M3: Spindle (cw), M4: Spindle (ccw), M5: Spindle off
            - 'coolant': M7: Mist coolant, M8: Flood coolant, M9: Coolant off, [M7,M8]: Both on
        """
        return self._state['parserstate']['modal']

    def get_feedrate(self) -> float:
        """Returns the GRBL device's current feed rate."""
        return self._state['parserstate']['feedrate']

    def get_spindle(self) -> float:
        """Returns the GRBL device's current spindle speed."""
        return self._state['parserstate']['spindle']

    def get_tool(self) -> int:
        """Returns the GRBL device's current tool."""
        return self._state['parserstate']['tool']

    def get_status_report(self):
        """Returns a status report of the device."""
        return self._state['status']

    def get_parser_state(self):
        """Returns the current status of the Gcode parser."""
        return self._state['parserstate']

    # Checkers

    def _check_active_state(self, state: GrblActiveState) -> bool:
        """Helper method to check the active state."""
        return self._state['status'].get('activeState') == state.value

    def is_alarm(self) -> bool:
        """Checks if the GRBL device is currently in ALARM state."""
        return self._check_active_state(GrblActiveState.ALARM)

    def is_idle(self) -> bool:
        """Checks if the GRBL device is currently in IDLE state."""
        return self._check_active_state(GrblActiveState.IDLE)

    def is_checkmode(self) -> bool:
        """Returns if the GRBL device is currently configured in check mode."""
        return self._check_active_state(GrblActiveState.CHECK)

    def connected(self) -> bool:
        return self.get_flag(GrblStatusFlag.CONNECTED.value)

    def paused(self) -> bool:
        return self.get_flag(GrblStatusFlag.PAUSED.value)

    def finished(self) -> bool:
        """Checks if the program has finished (M2/M30)."""
        return self.get_flag(GrblStatusFlag.FINISHED.value)

    def failed(self) -> bool:
        """Checks if the controller has encountered an error."""
        return self._error_line is not None

    # Utilities

    def get_error_message(self):
        if not self.failed():
            return

        error_message = 'There was an error'

        if self.is_alarm():
            error_message = 'An alarm was triggered'

        return (
            f'{error_message} (code: {self._error_data["code"]}) '
            f'while executing line: {self._error_line}\n'
            f'{self._error_data["message"]}:{self._error_data["description"]}'
        )
