import re

from core.utilities.grbl.parsers.grblMsgTypes import GRBL_RESULT_OK
from core.utilities.grbl.parsers.grblParserGeneric import GrblParserGeneric


class GrblParserResultOk(GrblParserGeneric):
    """Detects a successful GRBL response.

    Example:
        - ok
    """

    @staticmethod
    def parse(line):
        matches = re.match(r"^ok$", line)

        if not matches:
            return None

        return GRBL_RESULT_OK, {}
