import re
from typing import Optional

# Type alias for a parsed log entry.
# Fields: (datetime_str, level, type_or_None, message)
Log = tuple[str, str, Optional[str], str]


def interpret_log(log: str) -> Optional[Log]:
    """Parse a single log line.

    Expected format::

        [DD/MM/YYYY hh:mm:ss] LEVEL: [TYPE?] Message

    Returns:
        A ``Log`` tuple on success, ``None`` if the line does not match.
    """
    log_regex = r"^\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\] (\w+): (.+)$"
    log_match = re.search(log_regex, log)
    if not log_match:
        return None

    msg_regex = r"^(?:\[(\w+)\] )?(.+)$"
    msg_match = re.search(msg_regex, log_match.group(3))
    if not msg_match:
        return None

    return (
        log_match.group(1),
        log_match.group(2),
        msg_match.group(1),
        msg_match.group(2),
    )
