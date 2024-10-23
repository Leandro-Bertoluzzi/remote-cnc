from core.utils.files import getFilesInFolder
from core.utils.loggerFactory import LOGS_DIR, LOGS_DATETIME_FORMAT
from core.utils.logsInterpreter import LogsInterpreter
import csv
from datetime import datetime
import io
from pathlib import Path
import re
from schemas.logs import LogsResponse

_LOG_FILE_FIXED_NAMES = {
    "celery.log": "Registros del worker",
    "cnc_server.log": "Streaming de CNC server",
    "control_view.log": "Streaming de Control view",
}


def classify_log_files() -> list[LogsResponse]:
    log_files = getFilesInFolder(LOGS_DIR)
    classified_files = []

    for file in log_files:
        description = ""

        if file.startswith('task_'):
            # task_{formatted_name}_{YYYYMMDD_hhmmss}.log
            file_regex = r'^task_(\w+)_(\d{8}_\d{6})\.log$'
            log_matches = re.search(file_regex, file)

            source_file = log_matches.group(1)
            date_string = log_matches.group(2)

            date_time = datetime.strptime(date_string, LOGS_DATETIME_FORMAT)
            date = date_time.strftime('%d/%m/%Y')
            time = date_time.strftime('%H:%M:%S')

            description = f"Ejecución del archivo <<{source_file}>> el día {date} a las {time}"
        elif file in _LOG_FILE_FIXED_NAMES.keys():
            description = _LOG_FILE_FIXED_NAMES[file]

        classified_files.append({
            'file_name': file,
            'description': description
        })

    return classified_files


def generate_log_csv(log_path: Path) -> str:
    # Create a BytesIO object
    csv_file = io.StringIO()
    # Use the csv.writer to write the list to the BytesIO object
    csv_writer = csv.writer(csv_file)

    headers = ['Fecha y hora', 'Nivel', 'Tipo', 'Mensaje']
    csv_writer.writerow(headers)

    logs = LogsInterpreter.interpret_file(log_path)

    for log in logs:
        csv_writer.writerow(list(log))

    # Return generated CSV
    return csv_file.getvalue()
