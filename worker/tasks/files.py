from app import app
from config import IMAGES_FOLDER_PATH
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import FileRepository
from core.utils.files import getFilePath
from utils.gcode2png import GcodeRenderer


@app.task(name='create_thumbnail', ignore_result=True)
def createThumbnail(
    file_id: int,
    base_path: str
) -> bool:
    db_session = SessionLocal()
    repository = FileRepository(db_session)

    # 1. Get the requested file
    file = repository.get_file_by_id(file_id)
    if not file:
        raise Exception('No se encontró el archivo en la base de datos')

    file_path = getFilePath(base_path, file.user_id, file.file_name)

    # 2. Instantiate the G-code renderer
    renderer = GcodeRenderer()

    # 3. Generate the thumbnail and save it to images folder
    output = IMAGES_FOLDER_PATH + "/img" + str(file.id) + ".png"
    renderer.run(file_path, output, moves=False)
