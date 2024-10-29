import re
from utilities.grbl.parsers.grblParserGeneric import GrblParserGeneric
from utilities.grbl.parsers.grblMsgTypes import GRBL_MSG_VERSION


class GrblParserMsgVersion(GrblParserGeneric):
    """Detects a GRBL version message, initiated by the user via a `$I` print help command.
    It always goes together with the option message [OPT: ].

    [VER:] and [OPT:] Indicate build info data from a $I user query.
    These build info messages are followed by an ok to confirm the $I was executed

    Example:
        - [VER:1.1d.20161014:]
        - [VER:1.1d.20161014:Some string]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:VER:)(.+)\]$', line)

        if (not matches):
            return None

        # Use the colons (:) to split the values, ignoring the last character "]"
        values = re.split(r':', line[:-1])

        payload = {
            'version': values[1],
            'comment': values[2]
        }

        return GRBL_MSG_VERSION, payload
