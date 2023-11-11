import re
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_STARTUP

class GrblParserMsgStartup(GrblParserGeneric):
    """Detects a GRBL startup (welcome) message.

    Examples:
        - Grbl 0.9j ['$' for help]
        - Grbl 1.1d ['$' for help]
        - Grbl 1.1
        - Grbl 1.1h: LongMill build ['$' for help]
        - Grbl 1.1h ['$' for help] LongMill build Feb 25, 2020
        - myCustomGrbl 2.0.0 ['$' for help]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^([a-zA-Z0-9]+)\s+((?:\d+\.){1,2}\d+[a-zA-Z0-9\-\.]*)([^\[]*\[[^\]]+\].*)?', line)

        if (not matches):
            return None

        payload = {
            'firmware' : matches.group(1),
            'version' : matches.group(2),
            'message' : matches.group(3)
        }

        return GRBL_MSG_STARTUP, payload
