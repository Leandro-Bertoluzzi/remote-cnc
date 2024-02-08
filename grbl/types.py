from typing import Any, List, Dict, Optional
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
GrblControllerSettings = TypedDict('GrblControllerSettings', {
    'version': str,
    'parameters': Any,
    'checkmode': bool
})
GrblResponse = tuple[Optional[str], dict[str, str]]
