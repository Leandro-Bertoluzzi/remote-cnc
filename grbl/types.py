from typing import List, Dict, Optional
from typing_extensions import TypedDict

# Definition of types

ModalGroup = TypedDict('ModalGroup', {'group': str, 'modes': List[str]})
GrblError = TypedDict('GrblError', {'code': int, 'message': str, 'description': str})
GrblSetting = TypedDict('GrblSetting', {
    'value': str,
    'message': str,
    'units': str,
    'description': str
})
GrblSettings = dict[str, GrblSetting]

Coordinates = Dict[str, float]
Status = TypedDict('Status', {
    'activeState': str,
    'subState': Optional[int],
    'mpos': Coordinates,
    'wpos': Coordinates,
    'ov': List[int],
    'wco': Coordinates,
    'pinstate': Optional[str],
    'buffer': Optional[Dict[str, int]],
    'line': Optional[int],
    'accessoryState': Optional[str]
})

ParserState = TypedDict('ParserState', {
    'modal': Dict[str, str],
    'tool': int,
    'feedrate': float,
    'spindle': float
})
GrblControllerState = TypedDict('GrblControllerState', {
    'status': Status,
    'parserstate': ParserState
})

ProbeStatus = TypedDict('ProbeStatus', {
    'x': float,
    'y': float,
    'z': float,
    'result': bool
})
GrblControllerParameters = TypedDict('GrblControllerParameters', {
    'G54': Coordinates,
    'G55': Coordinates,
    'G56': Coordinates,
    'G57': Coordinates,
    'G58': Coordinates,
    'G59': Coordinates,
    'G28': Coordinates,
    'G30': Coordinates,
    'G92': Coordinates,
    'TLO': float,
    'PRB': ProbeStatus
})
GrblBuildInfo = TypedDict('GrblBuildInfo', {
    'version': str,
    'comment': str,
    'optionCode': str,
    'blockBufferSize': int,
    'rxBufferSize': int
})
GrblResponse = tuple[Optional[str], dict[str, str]]
