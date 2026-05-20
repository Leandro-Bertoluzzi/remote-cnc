import re

from gateway.adapters.cnc.constants import GRBL_ALARMS
from gateway.adapters.cnc.parsers.grblMsgTypes import GRBL_MSG_ALARM
from gateway.adapters.cnc.parsers.grblParserGeneric import GrblParserGeneric
from gateway.adapters.cnc.types import GrblError


class GrblParserMsgAlarm(GrblParserGeneric):
    """Detects a GRBL ALARM message.

    Example:
        - ALARM: XX
    """

    @staticmethod
    def parse(line):
        matches = re.search(r"^ALARM:\s*(.+)$", line)

        if not matches:
            return None

        code = matches.group(1)
        # Find dictionary matching value in list
        alarm = None
        for el in GRBL_ALARMS:
            if el["code"] == int(code):
                alarm = el
                break

        payload: GrblError = {
            "code": int(code),
            "message": alarm["message"] if alarm else "",
            "description": alarm["description"] if alarm else "",
        }

        return GRBL_MSG_ALARM, payload
