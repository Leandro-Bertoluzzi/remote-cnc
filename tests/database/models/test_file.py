from database.models.file import File
from datetime import datetime

def test_file():
    # Auxiliary variables
    now = datetime(2023, 7, 20)

    # Instantiate file
    file = File(user_id=1, file_name='example_file.gcode', file_path='path/example_file.gcode', created_at=now)

    # Validate file fields
    assert file.user_id == 1
    assert file.file_name == 'example_file.gcode'
    assert file.file_path == 'path/example_file.gcode'
    assert file.created_at == datetime(2023, 7, 20)

    assert file.__repr__() == '<File: example_file.gcode, path: path/example_file.gcode, user ID: 1, created at: 2023-07-20 00:00:00>'

