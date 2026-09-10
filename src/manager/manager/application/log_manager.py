"""Application-layer log management use cases.

Provides log file classification, export and parsing functionalities.
Depends on an ILogStorage implementation for file access.
"""

import csv
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Generator

from core.config import LOGS_DATETIME_FORMAT
from core.domain.logs import Log, interpret_log
from core.ports.log_storage import ILogStorage


class LogManager:
    """Application service for log management use cases."""

    _LOG_FILE_FIXED_NAMES: dict[str, str] = {
        "worker.log": "Registros del worker",
        "controller.log": "Registros del controlador grbl",
        "gateway.log": "Streaming de CNC gateway",
    }

    def __init__(self, log_storage: ILogStorage):
        self.log_storage = log_storage

    def get_log_path(self, file_name: str) -> Path:
        """Return the absolute path for a log file name."""
        return self.log_storage.get_log_path(file_name)

    def log_exists(self, file_name: str) -> bool:
        """Return True if a log file with *file_name* exists in storage."""
        return self.log_storage.log_exists(file_name)

    def classify_log_files(self) -> list[dict]:
        """Return a list of log file descriptors with human-readable descriptions.

        Each entry is a dict with keys ``file_name`` and ``description``.

        Two categories are recognised:

        * **Task logs** — ``task_{name}_{YYYYMMDD_hhmmss}.log`` files created by
        ``setup_task_logger``. The description includes the source filename and
        execution timestamp.
        * **Fixed logs** — well-known filenames mapped in ``_LOG_FILE_FIXED_NAMES``.
        """
        log_files = self.log_storage.get_all_log_paths()
        classified: list[dict] = []

        for file in log_files:
            if not file.endswith(".log"):
                continue

            description = ""

            if file.startswith("task_"):
                # task_{formatted_name}_{YYYYMMDD_hhmmss}.log
                match = re.search(r"^task_(\w+)_(\d{8}_\d{6})\.log$", file)
                if not match:
                    continue

                source_file = match.group(1)
                date_time = datetime.strptime(match.group(2), LOGS_DATETIME_FORMAT)
                date = date_time.strftime("%d/%m/%Y")
                time = date_time.strftime("%H:%M:%S")
                description = f"Ejecución del archivo <<{source_file}>> el día {date} a las {time}"

            elif file in self._LOG_FILE_FIXED_NAMES:
                description = self._LOG_FILE_FIXED_NAMES[file]

            classified.append({"file_name": file, "description": description})

        return classified

    def generate_log_csv(self, log_name: str) -> str:
        """Parse the log file with *log_name* and return its contents as a CSV string.

        Columns: ``Fecha y hora``, ``Nivel``, ``Tipo``, ``Mensaje``.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Fecha y hora", "Nivel", "Tipo", "Mensaje"])

        for entry in self.interpret_file(log_name):
            writer.writerow(list(entry))

        return output.getvalue()

    def interpret_file(self, log_name: str) -> Generator[Log, None, None]:
        """Yield parsed log entries from *log_name*, skipping unparseable lines.

        Args:
            log_name: Name of the ``.log`` file.

        Yields:
            ``Log`` tuples for every valid line.
        """
        if not self.log_exists(log_name):
            return

        with self.log_storage.open_for_reading(log_name) as logs:
            for line in logs:
                parsed = interpret_log(line)
                if parsed:
                    yield parsed
