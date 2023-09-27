import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_RESULT_ERROR

class GrblParserResultError(GrblParserGeneric):
    """Detects an error GRBL response.

    Example:
        - error: XX
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^error:\s*(.+)$', line)

        if (not matches):
            return None

        payload = {
            'code': matches.group(1)
        }

        return GRBL_RESULT_ERROR, payload
