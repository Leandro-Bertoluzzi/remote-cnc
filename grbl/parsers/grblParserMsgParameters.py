import re
from ..parsers.grblParserGeneric import GrblParserGeneric
from ..parsers.grblMsgTypes import GRBL_MSG_PARAMS

class GrblParserMsgParameters(GrblParserGeneric):
    """Detects a GRBL parameters response, initiated by the user via a `$#` print help command.

    Each line of the printout starts with the data type, a `:`, and followed by the data values.
    If there is more than one, the order is  `XYZ` axes, separated by commas.

    The `PRB:` probe parameter message includes an additional `:` and suffix value is a boolean.
    It denotes whether the last probe cycle was successful or not.

    Example:
        [G54:0.000,0.000,0.000]
        [G55:0.000,0.000,0.000]

        ...
        [TLO:0.000]
        [PRB:0.000,0.000,0.000:0]
    """
    @staticmethod
    def parse(line):
        matches = re.search(r'^\[(G54|G55|G56|G57|G58|G59|G28|G30|G92|TLO|PRB):(.+)\]$', line)

        if (not matches):
            return None

        # Gxx, TLO or PRB
        name = matches.group(1)
        value = matches.group(2)

        payload = {
            'name': name
        }

        # [Gxx:0.000]
        if (re.search(r'^G\d+$', name)):
            axes = ['x', 'y', 'z']
            values = value.split(',')
            payload['value'] = {}
            for i in range(len(values)):
                payload['value'][axes[i]] = float(values[i])

        # [TLO:0.000]
        if (name == 'TLO'):
            payload['value'] = float(value)

        # [PRB:0.000,0.000,1.492:1]
        if (name == 'PRB'):
            axes = ['x', 'y', 'z']
            [valuesStr, result] = value.split(':')
            values = valuesStr.split(',')
            payload['value'] = {}
            for i in range(len(values)):
                payload['value'][axes[i]] = float(values[i])
            payload['value']['result'] = (result == '1')

        return GRBL_MSG_PARAMS, payload
