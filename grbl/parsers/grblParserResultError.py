import re
from ..constants import GRBL_ERRORS
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_RESULT_ERROR
from ..types import GrblError


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

        payload: GrblError = {
            'code': int(code),
            'message': error['message'] if error else '',
            'description': error['description'] if error else ''
        }

        return GRBL_RESULT_ERROR, payload
