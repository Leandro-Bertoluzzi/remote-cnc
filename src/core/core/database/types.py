from typing import Literal
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
    'tools': list[str],
    'max_feedrate': int,
    'commands_usage': dict[str, int],
    'unsupported_commands': list[str]
})
