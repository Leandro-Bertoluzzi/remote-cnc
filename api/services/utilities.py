from core.utils.files import getFilesInFolder
from core.utils.loggerFactory import LOGS_DIR, LOGS_DATETIME_FORMAT
from datetime import datetime
import re
from schemas.logs import LogsResponseModel


def serializeList(listToSerialize):
    """Return object list in an easily serializable format"""
    return [item.serialize() for item in listToSerialize]


def classify_log_files() -> list[LogsResponseModel]:
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

        if file == "celery.log":
            description = "Registros del worker"

        if file == "cnc_server.log":
            description = "Streaming de CNC server"

        if file == "control_view.log":
            description = "Streaming de Control view"

        classified_files.append({
            'file_name': file,
            'description': description
        })

    return classified_files
