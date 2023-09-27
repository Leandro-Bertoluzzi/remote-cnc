import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_MSG_ALARM

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

        payload = {
            'code': matches.group(1)
        }

        return GRBL_MSG_ALARM, payload
