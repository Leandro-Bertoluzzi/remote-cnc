"""Celery task wrappers for G-code file processing.

This module is the **composition root** for file-processing tasks:
it builds concrete infrastructure adapters and delegates all application
logic to the handlers.

No business logic lives here — add it to the handlers instead.
"""

from core.adapters.database.base import SessionLocal
from core.adapters.database.file_repository import FileRepository
from core.adapters.file_storage import FileSystemStorage
from core.config import FILES_FOLDER_PATH, IMAGES_FOLDER_PATH
from worker.adapters.rendering.gcode_renderer import GcodeRenderer
from worker.application.files_handler import (
    create_thumbnail_handler,
    generate_file_report_handler,
)
from worker.domain.gcode.constants import GRBL_VALID_GCODES, GRBL_VALID_MCODES
from worker.main import app


@app.task(name="create_thumbnail", ignore_result=True)
def createThumbnail(file_id: int) -> None:
    """Celery entry-point: build adapters and run the thumbnail handler."""
    db_session = SessionLocal()
    try:
        create_thumbnail_handler(
            file_id=file_id,
            repo=FileRepository(db_session),
            storage=FileSystemStorage(FILES_FOLDER_PATH),
            images_folder=IMAGES_FOLDER_PATH,
            renderer=GcodeRenderer(),
        )
    finally:
        db_session.close()


@app.task(name="generate_report", ignore_result=True)
def generateFileReport(file_id: int) -> None:
    """Celery entry-point: build adapters and run the file-report handler."""
    db_session = SessionLocal()
    try:
        generate_file_report_handler(
            file_id=file_id,
            repo=FileRepository(db_session),
            storage=FileSystemStorage(FILES_FOLDER_PATH),
            valid_gcodes=GRBL_VALID_GCODES,
            valid_mcodes=GRBL_VALID_MCODES,
        )
    finally:
        db_session.close()
