import re
from ..constants import GRBL_MODAL_GROUPS
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_PARSER_STATE


def findGroup(code: str) -> str:
    for element in GRBL_MODAL_GROUPS:
        if code in element['modes']:
            return element['group']
    return ''


class GrblParserMsgParserState(GrblParserGeneric):
    """Detects a GRBL G-code Parser State Message, initiated by the user via a `$G` command.
    The shown g-code are the current modal states of Grbl's g-code parser.

    This may not correlate to what is executing since there are usually several motions
    queued in the planner buffer.

    Example:
        - [GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0.0 S0]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(?:GC:)?((?:[a-zA-Z][0-9]+(?:\.[0-9]*)?\s*)+)\]$', line)

        if (not matches):
            return None

        words_not_trimmed = matches.group(1).split(' ')
        words = map(str.strip, words_not_trimmed)

        payload = {'modal': {}}

        for word in words:
            if word[0] == 'G' or word[0] == 'M':
                group = findGroup(word)
                try:
                    prevWord = payload['modal'][group]
                    payload['modal'][group] = [prevWord, word]
                except Exception:
                    payload['modal'][group] = word
            if word[0] == 'T':
                payload['tool'] = int(word[1:])
            if word[0] == 'F':
                payload['feedrate'] = float(word[1:])
            if word[0] == 'S':
                payload['spindle'] = float(word[1:])

        return GRBL_MSG_PARSER_STATE, payload
