from typing import Dict, Literal, List
from typing_extensions import TypedDict

StatusType = Literal[
    'pending_approval',
    'on_hold',
    'in_progress',
    'finished',
    'failed',
    'cancelled'
]

RoleType = Literal['user', 'admin']

FileReport = TypedDict('FileReport', {
    'total_lines': int,
    'pause_count': int,
    'movement_lines': int,
    'comment_count': int,
    'tools': List[str],
    'max_feedrate': int,
    'commands_usage': Dict[str, int],
    'unsupported_commands': List[str]
})
