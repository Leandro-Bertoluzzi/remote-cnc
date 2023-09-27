import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_MSG_ECHO

class GrblParserMsgEcho(GrblParserGeneric):
    """Detects a GRBL echo message.
    These messages indicate an automated line echo from a pre-parsed string prior to g-code parsing.
    Enabled by a config.h option, and often used for debugging communication issues.

    Example:
        - [echo:G1X0.540Y10.4F100]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:echo:)(.+)\]$', line)

        if (not matches):
            return None

        payload = {
            'message': matches.group(1)
        }

        return GRBL_MSG_ECHO, payload
