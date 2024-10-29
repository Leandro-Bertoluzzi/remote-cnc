import re
from utilities.grbl.constants import GRBL_ALARMS
from utilities.grbl.parsers.grblParserGeneric import GrblParserGeneric
from utilities.grbl.parsers.grblMsgTypes import GRBL_MSG_ALARM
from utilities.grbl.types import GrblError


class GrblParserMsgAlarm(GrblParserGeneric):
    """Detects a GRBL ALARM message.

    Example:
        - ALARM: XX
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^ALARM:\s*(.+)$', line)

        if (not matches):
            return None

        code = matches.group(1)
        # Find dictionary matching value in list
        alarm = None
        for el in GRBL_ALARMS:
            if el['code'] == int(code):
                alarm = el
                break

        payload: GrblError = {
            'code': int(code),
            'message': alarm['message'] if alarm else '',
            'description': alarm['description'] if alarm else ''
        }

        return GRBL_MSG_ALARM, payload
