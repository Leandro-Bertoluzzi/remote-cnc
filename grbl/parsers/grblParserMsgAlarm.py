import re
from ..constants import GRBL_ALARMS
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_ALARM


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

        payload = {
            'code': code,
            'message': alarm['message'] if alarm else '',
            'description': alarm['description'] if alarm else ''
        }

        return GRBL_MSG_ALARM, payload
