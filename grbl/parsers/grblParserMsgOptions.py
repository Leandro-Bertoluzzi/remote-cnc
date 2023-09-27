import re
from grbl.parsers.grblParserGeneric import GrblParserGeneric
from grbl.parsers.grblMsgTypes import GRBL_MSG_OPTIONS

class GrblParserMsgOptions(GrblParserGeneric):
    """Detects a GRBL compile-time options message, initiated by the user via a `$I` print help command.
    It always goes together with the version message [VER: ].

    [VER:] and [OPT:] Indicate build info data from a $I user query.
    These build info messages are followed by an ok to confirm the $I was executed

    Example:
        - [OPT:,15,128]
        - [OPT:VL,15,128]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:OPT:)(.+)\]$', line)

        if (not matches):
            return None

        # Use the commas (,) to split the values, ignoring the first "[OPT:" and the last character "]"
        values = re.split(r',', line[5:-1])

        payload = {
            'optionCode': values[0],
            'blockBufferSize': values[1],
            'rxBufferSize': values[2]
        }

        return GRBL_MSG_OPTIONS, payload
