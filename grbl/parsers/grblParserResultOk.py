import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_RESULT_OK

class GrblParserResultOk(GrblParserGeneric):
    """Detects a successful GRBL response.

    Example:
        - ok
    """
    @staticmethod
    def parse(line):
        matches = re.match(r'^ok$', line)

        if (not matches):
            return None

        payload = {}

        return GRBL_RESULT_OK, payload
