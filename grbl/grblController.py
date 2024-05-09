import logging
from serial import SerialException
from typing import Optional
from .grblLineParser import GrblLineParser
from .grblMonitor import GrblMonitor
from .grblStatus import GrblStatus, FLAG_CONNECTED, FLAG_STOP, FLAG_FINISHED, FLAG_PAUSED, \
    FLAG_ALARM
from .grblUtils import build_jog_command, get_grbl_setting
from .parsers.grblMsgTypes import GRBL_MSG_ALARM, GRBL_MSG_FEEDBACK, GRBL_MSG_HELP, \
    GRBL_MSG_OPTIONS, GRBL_MSG_PARSER_STATE, GRBL_MSG_PARAMS, GRBL_MSG_SETTING, \
    GRBL_MSG_STARTUP, GRBL_MSG_STATUS, GRBL_MSG_VERSION, GRBL_RESULT_ERROR, GRBL_RESULT_OK
from queue import Empty, Queue
import sys
import threading
import time
from .types import GrblControllerParameters, \
    GrblSetting, GrblSettings, GrblBuildInfo

try:
    from ..config import GRBL_SIMULATION
    from ..utils.serial import SerialService
except ImportError:
    from config import GRBL_SIMULATION
    from utils.serial import SerialService

# Constants
DISCONNECTED = 'DISCONNECTED'
SERIAL_POLL = 0.125  # seconds
SERIAL_TIMEOUT = 0.10  # seconds
G_POLL = 10  # seconds
RX_BUFFER_SIZE = 128
GRBL_HELP_MESSAGE = '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x'


class GrblController:
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

    def __init__(self, logger: logging.Logger):
        # Configure serial interface
        self.serial = SerialService()
        self.queue: Queue[str] = Queue()        # Command queue to be sent to GRBL
        self.serial_thread: Optional[threading.Thread] = None

        # Configure logger
        self.grbl_monitor = GrblMonitor(logger)

        # Configure status manager
        self.grbl_status = GrblStatus()

        # State variables
        self._sumcline = 0          # Amount of bytes in GRBL buffer
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
        self.grbl_monitor.received(response, msgType, payload)

        if not GRBL_SIMULATION:
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
            self.grbl_monitor.warning('Homing cycle required at startup, handling...')
            self.handleHomingCycle()

        # State variables
        self.grbl_status.set_flag(FLAG_CONNECTED, True)
        self.grbl_status.set_flag(FLAG_FINISHED, False)
        self.commands_count = 0

        # Start serial communication
        self.serial_thread = threading.Thread(target=self.serialIO)
        self.serial_thread.start()

        return responsePayload

    def disconnect(self):
        """Ends the communication with the GRBL device.
        """
        if not self.grbl_status.connected():
            return

        # Stops communication with serial port
        self.serial_thread = None
        self.serial.stopConnection()
        self.grbl_monitor.info('**Disconnected from device**')

        # State variables
        self.grbl_status.set_flag(FLAG_CONNECTED, False)
        self.grbl_status.set_active_state(DISCONNECTED)

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
            self._sumcline = sum(cline)
            self.commands_count += 1
            return

        if msgType == GRBL_RESULT_ERROR:
            self.setPaused(True)
            error_line = removeProcessedCommand()
            del payload['raw']
            self.grbl_status.set_error(error_line, payload)
            self.grbl_monitor.error(
                f"Error: {payload['message']}. Description: {payload['description']}"
            )
            return

        if msgType == GRBL_MSG_ALARM:
            self.grbl_status.set_flag(FLAG_ALARM, True)
            self.grbl_status.set_flag(FLAG_PAUSED, True)
            error_line = removeProcessedCommand()
            del payload['raw']
            self.grbl_status.set_error(error_line, payload)
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
            self.grbl_status.update_parser_state(payload)
            self.grbl_monitor.debug(
                f"Parser state was successfully updated to {self.grbl_status.get_parser_state()}"
            )
            return

        if (msgType == GRBL_MSG_STATUS):
            del payload['raw']
            self.grbl_status.update_status(payload)
            self.grbl_monitor.debug(
                f"Device status was successfully updated to {self.grbl_status.get_status_report()}"
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
            self.grbl_status.set_flag(FLAG_ALARM, False)
            self.grbl_status.clear_error()
            self.grbl_monitor.info('Alarm was successfully disabled')
            return

        # Response to checkmode toggled
        if (msgType == GRBL_MSG_FEEDBACK):
            is_check_msg = 'Enabled' in payload['message'] or 'Disabled' in payload['message']
            if is_check_msg:
                checkmode = ('Enabled' in payload['message'])
                self.grbl_monitor.info(
                    f'Checkmode was successfully updated to {checkmode}'
                )
                return

        self.grbl_monitor.debug(f'Unprocessed message from GRBL: {response}')

    # INTERNAL STATE MANAGEMENT

    def restartCommandsCount(self):
        """Restart the count of already processed commands.
        """
        self.commands_count = 0

    def getCommandsCount(self):
        """Get the count of already processed commands.
        """
        return self.commands_count

    # ACTIONS

    def setPaused(self, paused: bool):
        self.grbl_status.set_flag(FLAG_PAUSED, paused)

        if paused:
            self.grbl_pause()
            return

        self.grbl_resume()

    def sendCommand(self, command: str):
        """Adds a GCODE line or a GRBL command to the serial queue.
        """
        tosend = command.strip()

        if not tosend:
            self.commands_count += 1
            return

        import re

        comment_pattern = re.compile(r'(^\(.*\)$)|(^;.*)')
        if comment_pattern.match(tosend):
            self.commands_count += 1
            return

        self.queue.put(tosend)

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

    def grbl_pause(self):
        """Feed Hold: Places Grbl into a suspend or HOLD state.
        If in motion, the machine will decelerate to a stop and then be suspended.
        """
        try:
            self.serial.sendBytes(b'!')
        except SerialException:
            self.grbl_monitor.error(
                f'Error sending command to GRBL: {str(sys.exc_info()[1])}'
            )
            return
        self.grbl_monitor.sent('!')
        self.grbl_monitor.info('Requested PAUSE')

    def grbl_resume(self):
        """Cycle Start / Resume: Resumes a feed hold, a safety door/parking state
        when the door is closed, and the M0 program pause states.
        """
        try:
            self.serial.sendBytes(b'~')
        except SerialException:
            self.grbl_monitor.error(
                f'Error sending command to GRBL: {str(sys.exc_info()[1])}'
            )
            return
        self.grbl_monitor.sent('~')
        self.grbl_monitor.info('Requested RESUME')

    def grbl_soft_reset(self):
        """Soft-Reset: Halts and safely resets Grbl without a power-cycle.
        - If reset while in motion, Grbl will throw an alarm to indicate position may be
        lost from the motion halt.
        - If reset while not in motion, position is retained and re-homing is not required.
        """
        try:
            self.serial.sendBytes(b'\x18')
        except SerialException:
            self.grbl_monitor.error(
                f'Error sending command to GRBL: {str(sys.exc_info()[1])}'
            )
            return
        self.grbl_monitor.sent('0x18')
        self.grbl_monitor.info('Requested STOP')

        # Tell the serialIO thread to stop streaming
        self.grbl_status.set_flag(FLAG_STOP, True)

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

    def getParameters(self):
        """Returns the GRBL device's current parameter data.
        """
        return self.parameters

    def getGrblSettings(self):
        """Returns a dictionary with the firmware settings.
        """
        return self.settings

    def getBuildInfo(self):
        """Returns the firmware's build information.
        """
        return self.build_info

    def getBufferFill(self) -> float:
        """Returns how filled the GRBL command buffer is as a percentage,
        useful to monitor buffer usage.
        """
        return self._sumcline * 100.0 / RX_BUFFER_SIZE

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
                and not self.grbl_status.paused()
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
            if self.grbl_status.get_flag(FLAG_STOP):
                self.emptyQueue()
                tosend = None
                self.grbl_status.set_flag(FLAG_STOP, False)
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
                    error_data = {
                        'code': 0,
                        'message': 'Communication error',
                        'description': str(sys.exc_info()[1])
                    }
                    self.grbl_status.set_error(tosend, error_data)
                    self.emptyQueue()
                    self.disconnect()
                    return
                self.grbl_monitor.sent(tosend)

                # Check if end of program
                if tosend.strip() in ['M2', 'M02', 'M30']:
                    self.grbl_monitor.info(f'A program end command was found: {tosend}')
                    self.grbl_status.set_flag(FLAG_FINISHED, True)
                    self.emptyQueue()
                    return

                tosend = None
                if t - tg > G_POLL:
                    self.queryGcodeParserState()
                    tg = t
