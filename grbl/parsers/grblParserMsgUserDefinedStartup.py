import re
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_USER_DEFINED_STARTUP

class GrblParserMsgUserDefinedStartup(GrblParserGeneric):
    """Detects a GRBL user-defined startup lines message, initiated by the user via a `$N` command.

    Example:
        - $N0=G54
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^(\$N[^=]+)=(.*)\s*', line)

        if (not matches):
            return None

        payload = {
            'name': matches.group(1),
            'value': matches.group(2)
        }

        return GRBL_MSG_USER_DEFINED_STARTUP, payload
