"""Infrastructure adapter for parsing log files produced by this application.

Reads and parses the structured log format written by the loggers.

Note: direct filesystem access is intentional for now. A future
``ILogStorage`` port would allow injecting a storage abstraction here,
following the same pattern as ``FileManager``.
"""

import os
from pathlib import Path
from typing import Generator

from core.domain.logs import Log, interpret_log


class LogsInterpreter:
    """Parse log files produced by the application loggers."""

    @classmethod
    def interpret_file(cls, file_path: Path) -> Generator[Log, None, None]:
        """Yield parsed log entries from *file_path*, skipping unparseable lines.

        Args:
            file_path: Path to the ``.log`` file.

        Yields:
            ``Log`` tuples for every valid line.
        """
        if not os.path.exists(file_path):
            return

        with open(file_path, "r") as logs:
            for line in logs:
                parsed = interpret_log(line)
                if parsed:
                    yield parsed
