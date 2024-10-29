import re
from utilities.grbl.parsers.grblParserGeneric import GrblParserGeneric
from utilities.grbl.parsers.grblMsgTypes import GRBL_MSG_HELP


class GrblParserMsgHelp(GrblParserGeneric):
    """Detects a GRBL help response, initiated by the user via a `$` print help command.

    Example:
        - [HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:HLP:)(.+)\]$', line)

        if (not matches):
            return None

        payload = {
            'message': matches.group(1)
        }

        return GRBL_MSG_HELP, payload
