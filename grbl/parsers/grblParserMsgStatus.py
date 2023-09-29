import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_MSG_STATUS

class GrblParserMsgStatus(GrblParserGeneric):
    """Detects a GRBL real-time status response, initiated by the user via a `?` status command.
    Only supports GRBL v1.1 !!

    Contains real-time data of Grbl's state, position, and other data required independently of the stream.

    Example:
        * GRBL v1.1
            - <Idle|MPos:3.000,2.000,0.000|FS:0,0>
            - <Hold:0|MPos:5.000,2.000,0.000|FS:0,0>
            - <Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>
            - <Idle|MPos:5.000,2.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
            - <Run|MPos:23.036,1.620,0.000|FS:500,0>
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^<(.+)>$', line)

        if (not matches):
            return None

        payload = {}
        result = {}
        params = matches.group(1).split('|')
        axes = ['x', 'y', 'z']

        # Active State (v1.1)
        # * Valid states types: Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
        # * Sub-states may be included via : a colon delimiter and numeric code.
        # * Current sub-states are:
        #   - Hold:0 Hold complete. Ready to resume.
        #   - Hold:1 Hold in-progress. Reset will throw an alarm.
        #   - Door:0 Door closed. Ready to resume.
        #   - Door:1 Machine stopped. Door still ajar. Can't resume until closed.
        #   - Door:2 Door opened. Hold (or parking retract) in-progress. Reset will throw an alarm.
        #   - Door:3 Door closed and resuming. Restoring from park, if applicable. Reset will throw an alarm.
        states = params[0].split(':')
        payload['activeState'] = states[0] or ''
        if len(states) > 1:
            payload['subState'] = int(states[1])

        # Identify fields
        for param in params:
            nv = re.search(r'^(.+):(.+)', param)
            if nv:
                type = nv.group(1)
                value = nv.group(2).split(',')
                result[type] = value

        # Machine position
        if 'MPos' in result.keys():
            mPos = result['MPos']
            payload['mpos'] = {}
            for i in range(len(mPos)):
                payload['mpos'][axes[i]] = float(mPos[i])

        # Work position
        if 'WPos' in result.keys():
            wPos = result['WPos']
            payload['wpos'] = {}
            for i in range(len(mPos)):
                payload['wpos'][axes[i]] = float(wPos[i])

        # Work Coordinate Offset
        if 'WCO' in result.keys():
            wco = result['WCO']
            payload['wco'] = {}
            for i in range(len(wco)):
                payload['wco'][axes[i]] = float(wco[i])

        # Ignored: Planner Buffer (v0.9)
        # Ignored: RX Buffer (v0.9)

        # Buffer State
        if 'Bf' in result.keys():
            payload['buffer'] = {}
            payload['buffer']['planner'] = int(result['Bf'][0])
            payload['buffer']['rx'] = int(result['Bf'][1])

        # Line number
        # Ln:99999 indicates line 99999 is currently being executed.
        if 'Ln' in result.keys():
            payload['line'] = int(result['Ln'][0])

        # Feed Rate
        # F:500 contains real-time feed rate data as the value.
        # This appears only when VARIABLE_SPINDLE is disabled.
        if 'F' in result.keys():
            payload['feedrate'] = float(result['F'][0])

        # Current Feed and Speed
        # FS:500,8000 contains real-time feed rate, followed by spindle speed, data as the values.
        if 'FS' in result.keys():
            payload['feedrate'] = float(result['FS'][0])
            payload['spindle'] = int(result['FS'][1])

        # Ignored: Limit pins (v0.9)

        # Input Pin State (v1.1)
        # * Pn:XYZPDHRS indicates which input pins Grbl has detected as 'triggered'.
        # * Each letter of XYZPDHRS denotes a particular 'triggered' input pin.
        # - X Y Z XYZ limit pins, respectively
        # - P the probe pin.
        # - D H R S the door, hold, soft-reset, and cycle-start pins, respectively.
        # - Example: Pn:PZ indicates the probe and z-limit pins are 'triggered'.
        # - Note: A may be added in later versions for an A-axis limit pin.
        if 'Pn' in result.keys():
            payload['pinstate'] = result['Pn'][0]

        # Override Values
        # Ov:100,100,100 indicates current override values in percent of programmed values for feed, rapids, and spindle speed, respectively.
        if 'Ov' in result.keys():
            payload['ov'] = [int(ov) for ov in result['Ov']]

        # Accessory State
        # * A:SFM indicates the current state of accessory machine components, such as the spindle and coolant.
        # * Each letter after A: denotes a particular state. When it appears, the state is enabled. When it does not appear, the state is disabled.
        # - S indicates spindle is enabled in the CW direction. This does not appear with C.
        # - C indicates spindle is enabled in the CCW direction. This does not appear with S.
        # - F indicates flood coolant is enabled.
        # - M indicates mist coolant is enabled.
        if 'A' in result.keys():
            payload['accessoryState'] = result['A'][0]

        return GRBL_MSG_STATUS, payload
