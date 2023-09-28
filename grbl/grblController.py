from grbl.constants import GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_IDLE
from grbl.grblLineParser import GrblLineParser
from grbl.parsers.grblMsgTypes import GRBL_MSG_ALARM, GRBL_MSG_FEEDBACK, GRBL_MSG_STARTUP, GRBL_RESULT_OK, GRBL_RESULT_ERROR
from utils.serial import SerialService
from serial import SerialException

class GrblController:
    state = {
        'status': {
            'activeState': '',
            'mpos': {
                'x': '0.000',
                'y': '0.000',
                'z': '0.000'
            },
            'wpos': {
                'x': '0.000',
                'y': '0.000',
                'z': '0.000'
            },
            'ov': []
        },
        'parserstate': {
            'modal': {
                'motion': 'G0', # G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
                'wcs': 'G54', # G54, G55, G56, G57, G58, G59
                'plane': 'G17', # G17: xy-plane, G18: xz-plane, G19: yz-plane
                'units': 'G21', # G20: Inches, G21: Millimeters
                'distance': 'G90', # G90: Absolute, G91: Relative
                'feedrate': 'G94', # G93: Inverse time mode, G94: Units per minute
                'program': 'M0', # M0, M1, M2, M30
                'spindle': 'M5', # M3: Spindle (cw), M4: Spindle (ccw), M5: Spindle off
                'coolant': 'M9' # M7: Mist coolant, M8: Flood coolant, M9: Coolant off, [M7,M8]: Both on
            },
            'tool': '',
            'feedrate': '',
            'spindle': ''
        }
    }

    settings = {
        'version': '',
        'parameters': {},
        'settings': {}
    }

    def __init__(self):
        self.serial = SerialService()

    def connect(self, port: str, baudrate: int) -> dict[str, str]:
        """Starts the GRBL device connected to the given port.
        """
        try:
            response = self.serial.startConnection(port, baudrate)
        except SerialException as error:
            raise Exception('Failed opening serial port, verify the connection and close any other connection you may have')

        msgType, payload = GrblLineParser.parse(response)
        print('[Received] Message type: ', msgType, '| Payload: ', payload)

        if msgType != GRBL_MSG_STARTUP:
            raise Exception('Failed starting connection with GRBL: ', payload)

        self.settings['version'] = payload['version']
        responsePayload = payload

        # -- Startup alarm message validation --
        # [MSG:'$H'|'$X' to unlock] - Alarm state is active at initialization.
        # This message serves as a reminder note on how to cancel the alarm state.
        # All g-code commands and some ‘$’ are blocked until the alarm state is cancelled via homing $H or unlocking $X.
        # Only appears immediately after the Grbl welcome message when initialized with an alarm.
        response = self.serial.readLine()
        msgType, payload = GrblLineParser.parse(response)
        print('[Received] Message type: ', msgType, '| Payload: ', payload)

        if (msgType == GRBL_MSG_FEEDBACK) and ('$H' in payload['message']):
            #responsePayload['homing'] = True
            self.handleHomingCycle()

        return responsePayload

    def disconnect(self):
        """Ends the communication with the GRBL device.
        """
        self.serial.stopConnection()

    def streamLine(self, line: str) -> dict[str, str]:
        """Sends a line of G-code to the GRBL device.
        """
        response = self.serial.streamLine(line)
        print('[Sent] ', line)
        msgType, payload = GrblLineParser.parse(response)
        print('[Received] Message type: ', msgType, '| Payload: ', payload)

        if msgType == GRBL_RESULT_ERROR:
            raise Exception('Error executing line: ' + payload['message'] + '. Description: ' + payload['description'])
        if msgType == GRBL_MSG_ALARM:
            raise Exception('Alarm activated: ' + payload['message'] + '. Description: ' + payload['description'])
        return payload

    def handleHomingCycle(self) -> bool:
        """Runs the GRBL device's homing cycle.
        """
        #self.sendCommand('$H')

        # Technical debt: Temporary solution, disable alarm
        response = self.sendCommand('$X')
        print('[Sent] $X')
        msgType, payload = GrblLineParser.parse(response)
        print('[Received] Message type: ', msgType, '| Payload: ', payload)

        if (msgType == GRBL_MSG_FEEDBACK) and ('Caution: Unlocked' in payload['message']):
            # ALARM disabled
            pass

        # Wait for 'ok' message
        response = self.serial.readLine()
        msgType, payload = GrblLineParser.parse(response)
        print('[Received] Message type: ', msgType, '| Payload: ', payload)

        if msgType == GRBL_RESULT_OK:
            return True

        raise Exception('There was an error handling the homing cycle.')

    def sendCommand(self, command: str) -> str:
        """Sends a GRBL command to the GRBL device.
        """
        return self.serial.streamLine(command)

    # GETTERS

    def getMachinePosition(self) -> dict[str, str]:
        """Returns the GRBL device's current machine position.

        Example: { 'x': '0.000', 'y': '0.000', 'z': '0.000' }
        """
        return self.state['status']['mpos']

    def getWorkPosition(self) -> dict[str, str]:
        """Returns the GRBL device's current work position.

        Example: { 'x': '0.000', 'y': '0.000', 'z': '0.000' }
        """
        return self.state['status']['wpos']

    def getModalGroup(self) -> dict[str, str]:
        """Returns the GRBL device's current modal state.

        Example: { 'motion': 'G0', 'wcs': 'G54', 'plane': 'G17', 'units': 'G21', 'distance': 'G90', 'feedrate': 'G94', 'program': 'M0', 'spindle': 'M5', 'coolant': 'M9' }

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

    def getTool(self) -> str:
        """Returns the GRBL device's current tool.
        """
        return self.state['parserstate']['tool']

    def getParameters(self):
        """Returns the GRBL device's current parameter data.

        Example: {
            'G54' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G55' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G56' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G57' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G58' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G59' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G28' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G30' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G92' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'TLO' : 0.000,
            'PRB' : { 'x': '0.000', 'y': '0.000', 'z': '0.000', 'result': True }
        }
        """
        return self.settings['parameters']

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
