from typing import Any, List, Dict, Optional
from typing_extensions import TypedDict

# Definition of types

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
GrblState = TypedDict('GrblState', {'status': Status, 'parserstate': ParserState})
GrblSettings = TypedDict('GrblSettings', {'version': str, 'parameters': Any, 'checkmode': bool})
GrblResponse = tuple[Optional[str], dict[str, str]]
