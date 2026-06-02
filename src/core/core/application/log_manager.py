"""Application-layer log management use cases.

Provides log file classification and CSV export — the two operations
exposed by the API log routes.

Note: direct filesystem access is intentional for now. A future
``ILogStorage`` port would allow injecting a storage abstraction here,
following the same pattern as ``FileManager``.
"""

import csv
import io
import re
from datetime import datetime
from pathlib import Path

from core.application.logs_interpreter import LogsInterpreter
from core.config import LOGS_DATETIME_FORMAT, LOGS_FOLDER_PATH
from core.utilities.files import getFilesInFolder

_LOG_FILE_FIXED_NAMES: dict[str, str] = {
    "worker.log": "Registros del worker",
    "controller.log": "Registros del controlador grbl",
    "gateway.log": "Streaming de CNC gateway",
}


def get_log_path(file_name: str) -> Path:
    """Return the absolute path for a log file name."""
    return Path(LOGS_FOLDER_PATH) / file_name


def classify_log_files() -> list[dict]:
    """Return a list of log file descriptors with human-readable descriptions.

    Each entry is a dict with keys ``file_name`` and ``description``.

    Two categories are recognised:

    * **Task logs** — ``task_{name}_{YYYYMMDD_hhmmss}.log`` files created by
      ``setup_task_logger``. The description includes the source filename and
      execution timestamp.
    * **Fixed logs** — well-known filenames mapped in ``_LOG_FILE_FIXED_NAMES``.
    """
    log_files = getFilesInFolder(LOGS_FOLDER_PATH)
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

        elif file in _LOG_FILE_FIXED_NAMES:
            description = _LOG_FILE_FIXED_NAMES[file]

        classified.append({"file_name": file, "description": description})

    return classified


def generate_log_csv(log_path: Path) -> str:
    """Parse *log_path* and return its contents as a CSV string.

    Columns: ``Fecha y hora``, ``Nivel``, ``Tipo``, ``Mensaje``.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fecha y hora", "Nivel", "Tipo", "Mensaje"])

    for entry in LogsInterpreter.interpret_file(log_path):
        writer.writerow(list(entry))

    return output.getvalue()
