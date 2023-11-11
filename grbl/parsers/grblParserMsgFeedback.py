import re
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_FEEDBACK

class GrblParserMsgFeedback(GrblParserGeneric):
    """Detects a GRBL non-queried feedback message.
    These messages may appear at any time and are not part of a query.

    https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface#feedback-messages

    Example:
        - Grbl v0.9: [Message]
        - Grbl v1.1: [MSG: Message]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:MSG:)?(.+)\]$', line)

        if (not matches):
            return None

        payload = {
            'message': matches.group(1)
        }

        return GRBL_MSG_FEEDBACK, payload
