import logging
from serial import SerialException
from typing import Optional
from .constants import GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_IDLE
from .grblLineParser import GrblLineParser
from .grblMonitor import GrblMonitor
from .grblUtils import build_jog_command, get_grbl_setting
from .parsers.grblMsgTypes import GRBL_MSG_ALARM, GRBL_MSG_FEEDBACK, GRBL_MSG_HELP, \
    GRBL_MSG_OPTIONS, GRBL_MSG_PARSER_STATE, GRBL_MSG_PARAMS, GRBL_MSG_SETTING, \
    GRBL_MSG_STARTUP, GRBL_MSG_STATUS, GRBL_MSG_VERSION, GRBL_RESULT_ERROR, GRBL_RESULT_OK
from queue import Empty, Queue
import sys
import threading
import time
from .types import GrblControllerState, GrblControllerParameters, \
    GrblSetting, GrblSettings, GrblBuildInfo

try:
    from ..utils.serial import SerialService
except ImportError:
    from utils.serial import SerialService

# Constants
DISCONNECTED = 'DISCONNECTED'
SERIAL_POLL = 0.125  # seconds
SERIAL_TIMEOUT = 0.10  # seconds
G_POLL = 10  # seconds
RX_BUFFER_SIZE = 128
GRBL_HELP_MESSAGE = '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x'


class GrblController:
    state: GrblControllerState = {
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
            'tool': 1,
            'feedrate': 0.0,
            'spindle': 0.0
        }
    }

    parameters: GrblControllerParameters = {
        'G54': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G55': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G56': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G57': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G58': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G59': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G28': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G30': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'G92': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'TLO': 0.000,
        'PRB': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'result': True}
    }

    build_info: GrblBuildInfo = {
        'version': '',
        'comment': '',
        'optionCode': '',
        'blockBufferSize': 15,
        'rxBufferSize': RX_BUFFER_SIZE
    }

    settings: GrblSettings = {}

    help_text = GRBL_HELP_MESSAGE
    alarm_code: Optional[int] = None
    error_line: Optional[str] = None

    def __init__(self, logger: logging.Logger):
        # Configure serial interface
        self.serial = SerialService()
        self.queue: Queue[str] = Queue()        # Command queue to be sent to GRBL
        self.serial_thread: Optional[threading.Thread] = None

        # Configure logger
        self.grbl_monitor = GrblMonitor(logger)

        # State variables
        self.connected = False      # Machine is connected
        self._stop = False          # Raise to stop current run
        self._finished = False      # Notification of program end (M2/M30)
        self._paused = False        # Machine is on Hold
        self._alarm = False         # Display alarm message
        self._sumcline = 0          # Amount of bytes in GRBL buffer
        self._checkmode = False     # Check mode enabled
        self.commands_count = 0     # Amount of already processed commands

    def connect(self, port: str, baudrate: int) -> dict[str, str]:
        """Starts the GRBL device connected to the given port.
        """
        try:
            response = self.serial.startConnection(port, baudrate, SERIAL_TIMEOUT)
        except SerialException:
            self.grbl_monitor.critical(
                f'Failed opening serial port {port} with a baudrate of {baudrate}',
                exc_info=True
            )
            raise Exception(
                f'Failed opening serial port {port}, '
                'verify and close any other connection you may have'
            )
        self.grbl_monitor.info(
            f'Started USB connection at port {port} with a baudrate of {baudrate}'
        )

        # Handle response
        msgType, payload = GrblLineParser.parse(response)

        if msgType != GRBL_MSG_STARTUP:
            self.grbl_monitor.critical('Failed starting connection with GRBL')
            raise Exception('Failed starting connection with GRBL: ', payload)

        self.build_info['version'] = payload['version']
        responsePayload = payload

        # -- Startup alarm message validation --
        # [MSG:'$H'|'$X' to unlock] - Alarm state is active at initialization.
        # This message serves as a reminder note on how to cancel the alarm state.
        # All g-code commands and some ‘$’ are blocked until the alarm state is cancelled
        # via homing $H or unlocking $X.
        # Only appears immediately after the Grbl welcome message when initialized with an alarm.
        try:
            response = self.serial.readLine()
        except SerialException:
            self.grbl_monitor.critical(
                f'Error reading response from GRBL: {str(sys.exc_info()[1])}'
            )
            self.serial.stopConnection()
            return
        msgType, payload = GrblLineParser.parse(response)

        if (msgType == GRBL_MSG_FEEDBACK) and ('$H' in payload['message']):
            # responsePayload['homing'] = True
            self.grbl_monitor.warning('Homing cycle required at startup, handling...')
            self.handleHomingCycle()

        # State variables
        self.connected = True
        self._finished = False
        self.commands_count = 0

        # Start serial communication
        self.serial_thread = threading.Thread(target=self.serialIO)
        self.serial_thread.start()

        return responsePayload

    def disconnect(self):
        """Ends the communication with the GRBL device.
        """
        if not self.connected:
            return

        # Stops communication with serial port
        self.serial_thread = None
        self.serial.stopConnection()
        self.grbl_monitor.info('**Disconnected from device**')

        # State variables
        self.connected = False
        self.setState(DISCONNECTED)

    def parseResponse(self, response: str, cline: list[int], sline: list[str]):
        """Process the response from GRBL and update controller state.
        """
        def removeProcessedCommand() -> str:
            if cline:
                del cline[0]
            if sline:
                return sline.pop(0)
            return ''

        msgType, payload = GrblLineParser.parse(response)
        self.grbl_monitor.received(response, msgType, payload)

        # Process parsed response
        if msgType == GRBL_RESULT_OK:
            removeProcessedCommand()
            self.commands_count += 1
            return

        if msgType == GRBL_RESULT_ERROR:
            self._stop = True
            self.error_line = removeProcessedCommand()
            self.grbl_monitor.error(
                f"Error: {payload['message']}. Description: {payload['description']}"
            )
            return

        if msgType == GRBL_MSG_ALARM:
            self._alarm = True
            self._stop = True
            self.alarm_code = int(payload['code'])
            self.error_line = removeProcessedCommand()
            self.grbl_monitor.critical(
                f"Alarm activated: {payload['message']}. Description: {payload['description']}"
            )
            return

        if (msgType == GRBL_MSG_PARAMS):
            name = payload['name']
            self.parameters[name] = payload['value']
            self.grbl_monitor.debug(
                f'Device parameters were successfully updated to {self.parameters}'
            )
            return

        if (msgType == GRBL_MSG_VERSION):
            self.build_info['version'] = payload['version']
            self.build_info['comment'] = payload['comment']
            return

        if (msgType == GRBL_MSG_OPTIONS):
            self.build_info['optionCode'] = payload['optionCode']
            self.build_info['blockBufferSize'] = int(payload['blockBufferSize'])
            self.build_info['rxBufferSize'] = int(payload['rxBufferSize'])
            return

        if (msgType == GRBL_MSG_HELP):
            self.help_text = payload['message']
            return

        if (msgType == GRBL_MSG_PARSER_STATE):
            del payload['raw']
            self.state['parserstate'].update(payload)
            self.grbl_monitor.debug(
                f"Parser state was successfully updated to {self.state['parserstate']}"
            )
            return

        if (msgType == GRBL_MSG_STATUS):
            del payload['raw']
            self.state['status'].update(payload)
            self.grbl_monitor.debug(
                f"Device status was successfully updated to {self.state['status']}"
            )
            return

        if (msgType == GRBL_MSG_SETTING):
            key = payload['name']
            setting = get_grbl_setting(key)
            if setting:
                value: GrblSetting = {
                    'value': payload['value'],
                    'message': setting['message'],
                    'units': setting['units'],
                    'description': setting['description'],
                }
                self.settings[key] = value

        # Response to alarm disable
        if (msgType == GRBL_MSG_FEEDBACK) and ('Caution: Unlocked' in payload['message']):
            self._alarm = False
            self.alarm_code = None
            self.error_line = None
            self.grbl_monitor.info('Alarm was successfully disabled')
            return

        # Response to checkmode toggled
        if (msgType == GRBL_MSG_FEEDBACK):
            is_check_msg = 'Enabled' in payload['message'] or 'Disabled' in payload['message']
            if is_check_msg:
                self._checkmode = ('Enabled' in payload['message'])
                self.grbl_monitor.info(
                    f'Checkmode was successfully updated to {self._checkmode}'
                )
                return

        self.grbl_monitor.debug(f'Unprocessed message from GRBL: {response}')

    # INTERNAL STATE MANAGEMENT

    def setState(self, state: str):
        self.state['status']['activeState'] = state

    def setPaused(self, paused: bool):
        self._paused = paused

    def restartCommandsCount(self):
        """Restart the count of already processed commands.
        """
        self.commands_count = 0

    def getCommandsCount(self):
        """Get the count of already processed commands.
        """
        return self.commands_count

    def alarm(self) -> bool:
        """Checks if an alarm was triggered.
        """
        return self._alarm

    def failed(self) -> bool:
        """Checks if the controller has encountered an error.
        """
        return not not self.error_line

    def finished(self) -> bool:
        """Checks if the program has finished (M2/M30).
        """
        return self._finished

    # ACTIONS

    def sendCommand(self, command: str):
        """Adds a GCODE line or a GRBL command to the serial queue.
        """
        self.queue.put(command)

    def handleHomingCycle(self):
        """Runs the GRBL device's homing cycle.
        """
        # self.sendCommand('$H')

        # Technical debt: Temporary solution, disable alarm
        self.disableAlarm()

    def disableAlarm(self):
        """Disables an alarm.
        """
        self.sendCommand('$X')

    def toggleCheckMode(self):
        """Enables/Disables the "check G-code" mode.

        With this mode enabled, the user can stream a G-code program to Grbl,
        where it will parse it, error-check it, and report ok's and errors
        without powering on anything or moving.
        """
        self.sendCommand('$C')

    def jog(
            self,
            x: float,
            y: float,
            z: float,
            feedrate: float, *,
            units=None,
            distance_mode=None,
            machine_coordinates=False
    ):
        """Executes a 'jog' action.

        JOG mode is also called jogging mode.
        In this mode, the CNC machine is used to operate manually.
        """
        jog_command = build_jog_command(
            x, y, z,
            feedrate,
            units=units,
            distance_mode=distance_mode,
            machine_coordinates=machine_coordinates
        )
        self.sendCommand(jog_command)

    def setSettings(self, settings: dict[str, str]):
        """Updates the value of the given GRBL settings.
        """
        for key, value in settings.items():
            self.sendCommand(f'{key}={value}')

    # REAL TIME COMMANDS

    def queryStatusReport(self):
        """Queries the GRBL device's current status.
        """
        try:
            self.serial.sendBytes(b'?')
        except SerialException:
            self.grbl_monitor.error(
                f'Error sending command to GRBL: {str(sys.exc_info()[1])}'
            )
            return
        self.grbl_monitor.sent('?', debug=True)

    # QUERIES

    def queryGcodeParserState(self):
        """Queries the GRBL device's current parser state.
        """
        self.sendCommand('$G')

    def queryGrblHelp(self):
        """Queries the GRBL 'help' message.
        This message contains all valid GRBL commands.
        """
        self.sendCommand('$')

    def queryGrblParameters(self):
        """Queries the GRBL device's current parameter data.
        """
        self.sendCommand('$#')

    def queryGrblSettings(self):
        """Queries the list of GRBL settings with their current values.
        """
        self.sendCommand('$$')

    def queryBuildInfo(self):
        """Queries some GRBL device's (firmware) build information.
        """
        self.sendCommand('$I')

    # GETTERS

    def getMachinePosition(self) -> dict[str, float]:
        """Returns the GRBL device's current machine position.

        Example: { 'x': 0.000, 'y': 0.000, 'z': 0.000 }
        """
        return self.state['status']['mpos']

    def getWorkPosition(self) -> dict[str, float]:
        """Returns the GRBL device's current work position.

        Example: { 'x': 0.000, 'y': 0.000, 'z': 0.000 }
        """
        return self.state['status']['wpos']

    def getModalGroup(self) -> dict[str, str]:
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
        return self.state['parserstate']['modal']

    def getFeedrate(self) -> float:
        """Returns the GRBL device's current feed rate.
        """
        return self.state['parserstate']['feedrate']

    def getSpindle(self) -> float:
        """Returns the GRBL device's current spindle speed.
        """
        return self.state['parserstate']['spindle']

    def getTool(self) -> int:
        """Returns the GRBL device's current tool.
        """
        return self.state['parserstate']['tool']

    def getParameters(self):
        """Returns the GRBL device's current parameter data.
        """
        return self.parameters

    def getStatusReport(self):
        """Returns a status report of the device.
        """
        return self.state['status']

    def getGcodeParserState(self):
        """Returns the current status of the Gcode parser.
        """
        return self.state['parserstate']

    def getGrblSettings(self):
        """Returns a dictionary with the firmware settings.
        """
        return self.settings

    def getBuildInfo(self):
        """Returns the firmware's build information.
        """
        return self.build_info

    def getCheckModeEnabled(self):
        """Returns if the GRBL device is currently configured in check mode.
        """
        return self._checkmode

    def getBufferFill(self) -> float:
        """Returns how filled the GRBL command buffer is as a percentage,
        useful to monitor buffer usage.
        """
        return self._sumcline * 100.0 / RX_BUFFER_SIZE

    def isAlarm(self) -> bool:
        """Checks if the GRBL device is currently in ALARM state.
        """
        activeState = self.state['status']['activeState']
        return activeState == GRBL_ACTIVE_STATE_ALARM

    def isIdle(self) -> bool:
        """Checks if the GRBL device is currently in IDLE state.
        """
        activeState = self.state['status']['activeState']
        return activeState == GRBL_ACTIVE_STATE_IDLE

    # Message queue management

    def emptyQueue(self):
        """Empty command queue.
        """
        while self.queue.qsize() > 0:
            try:
                self.queue.get_nowait()
            except Empty:
                break

    # Threads

    def serialIO(self):
        """Thread performing I/O on serial line.
        """
        cline: list[int] = []  # length of pipeline commands
        sline: list[str] = []  # pipeline commands
        tosend = None  # next string to send
        tr = tg = time.time()  # last time a ? or $G was send to grbl

        while self.serial_thread:
            t = time.time()

            # Refresh machine position?
            if t - tr > SERIAL_POLL:
                self.queryStatusReport()
                tr = t

            # Fetch new command to send if...
            if (
                tosend is None
                and not self._paused
                and self.queue.qsize() > 0
            ):
                try:
                    tosend = self.queue.get_nowait()
                except Empty:
                    break

                if tosend is not None:
                    # If necessary, all modifications in tosend should be
                    # done before adding it to cline

                    # Bookkeeping of the buffers
                    sline.append(tosend)
                    cline.append(len(tosend))

            # Anything to receive?
            if self.serial.waiting() or tosend is None:
                try:
                    response = self.serial.readLine()
                except SerialException:
                    self.grbl_monitor.error(
                        f'Error reading response from GRBL: {str(sys.exc_info()[1])}'
                    )
                    self.emptyQueue()
                    self.disconnect()
                    return

                if not response:
                    pass
                else:
                    self.parseResponse(response, cline, sline)

            # Received external message to stop
            if self._stop:
                self.emptyQueue()
                tosend = None
                self._stop = False
                self.grbl_monitor.info('STOP request processed')

            # Send command to GRBL
            if tosend is not None and sum(cline) < RX_BUFFER_SIZE:
                self._sumcline = sum(cline)

                try:
                    self.serial.sendLine(tosend)
                except SerialException:
                    self.grbl_monitor.error(
                        f'Error sending command to GRBL: {str(sys.exc_info()[1])}'
                    )
                    self.error_line = tosend
                    self.emptyQueue()
                    self.disconnect()
                    return
                self.grbl_monitor.sent(tosend)

                # Check if end of program
                if tosend.strip() in ['M2', 'M02', 'M30']:
                    self.grbl_monitor.info(f'A program end command was found: {tosend}')
                    self._finished = True
                    self.emptyQueue()
                    self.disconnect()
                    return

                tosend = None
                if t - tg > G_POLL:
                    self.queryGcodeParserState()
                    tg = t
