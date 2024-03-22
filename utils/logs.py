from pathlib import Path
from typing import Optional
import re

# Custom types
# Levels: 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'
# Types: 'SENT', 'RECEIVED', 'PARSED', None
Log = tuple[str, str, Optional[str], str]


# Classes

class LogsInterpreter:
    @classmethod
    def interpret_log(cls, log: str) -> Optional[Log]:
        # Parse log
        # [DD/MM/YYYY hh:mm:ss] LEVEL: Message
        log_regex = r'^\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\] (\w+): (.+)$'
        log_matches = re.search(log_regex, log)

        if (not log_matches):
            return None

        # Parse message
        # [TYPE?] Message
        msg_regex = r'^(?:\[(\w+)\] )?(.+)$'
        message = log_matches.group(3)
        msg_matches = re.search(msg_regex, message)

        return (
            log_matches.group(1),
            log_matches.group(2),
            msg_matches.group(1),
            msg_matches.group(2),
        )

    @classmethod
    def interpret_file(cls, file_path: Path) -> list[Log]:
        logs_list = []

        with open(file_path, "r") as logs:
            for log in logs:
                parsed = cls.interpret_log(log)
                if not parsed:
                    continue
                logs_list.append(parsed)

        return logs_list


class LogFileWatcher:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def set_file_path(self, file_path: Path):
        self.file_path = file_path

    def start_watching(self):
        pass

    def stop_watching(self):
        pass

