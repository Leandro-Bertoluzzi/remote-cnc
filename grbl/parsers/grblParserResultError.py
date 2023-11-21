import re
from ..constants import GRBL_ERRORS
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_RESULT_ERROR


class GrblParserResultError(GrblParserGeneric):
    """Detects an error GRBL response.

    Example:
        - error: XX
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^error:\s*(.+)$', line)

        if (not matches):
            return None

        code = matches.group(1)
        # Find dictionary matching value in list
        error = None
        for el in GRBL_ERRORS:
            if el['code'] == int(code):
                error = el
                break

        payload = {
            'code': code,
            'message': error['message'],
            'description': error['description']
        }

        return GRBL_RESULT_ERROR, payload
