"""Pure application-layer handlers for G-code file processing tasks.

This module contains NO concrete infrastructure imports. All dependencies
are received as ports (``typing.Protocol``).
"""

from core.ports.file_repository import IFileRepository
from core.ports.file_storage import IFileStorage
from worker.domain.gcode.analyser import GcodeAnalyser
from worker.ports.renderer import IRenderer


def create_thumbnail_handler(
    file_id: int,
    repo: IFileRepository,
    storage: IFileStorage,
    images_folder: str,
    renderer: IRenderer,
) -> None:
    """Generate a PNG thumbnail for a G-code file.

    Args:
        file_id: ID of the file to generate the thumbnail for.
        repo: File repository port.
        storage: File storage port (used to resolve the G-code file path).
        images_folder: Absolute path to the folder where thumbnails are saved.
        renderer: Thumbnail renderer.
    """
    # 1. Get the requested file
    file = repo.get_file_by_id(file_id)
    if not file:
        raise Exception("No se encontró el archivo en la base de datos")

    file_path = storage.get_file_path(file.user_id, file.file_name)

    # 2. Generate the thumbnail and save it to images folder
    output = images_folder + "/img" + str(file.id) + ".png"
    renderer.run(str(file_path), output, moves=False)


def generate_file_report_handler(
    file_id: int,
    repo: IFileRepository,
    storage: IFileStorage,
    valid_gcodes: list,
    valid_mcodes: list,
) -> None:
    """Analyse a G-code file and persist the generated report.

    Args:
        file_id: ID of the file to analyse.
        repo: File repository port (also accepts and stores the report).
        storage: File storage port (used to resolve the G-code file path).
        valid_gcodes: List of valid G-code words accepted by the parser.
        valid_mcodes: List of valid M-code words accepted by the parser.
    """
    # 1. Get the requested file
    file = repo.get_file_by_id(file_id)
    if not file:
        raise Exception("No se encontró el archivo en la base de datos")

    file_path = storage.get_file_path(file.user_id, file.file_name)

    # 2. Instantiate the G-code analyser
    analyser = GcodeAnalyser(file_path, valid_gcodes, valid_mcodes)

    # 3. Analyse and save the generated report
    report = analyser.analyse()
    repo.save_file_report(file_id, report)
