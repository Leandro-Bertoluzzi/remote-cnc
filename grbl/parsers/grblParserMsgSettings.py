import re
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_SETTING


class GrblParserMsgSettings(GrblParserGeneric):
    """Detects a GRBL settings message, initiated by the user via a `$$` settings print command.

    Example:
        - $x=val
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^(\$[^=]+)=([^ ]*)\s*', line)

        if (not matches):
            return None

        payload = {
            'name': matches.group(1),
            'value': matches.group(2)
        }

        return GRBL_MSG_SETTING, payload
