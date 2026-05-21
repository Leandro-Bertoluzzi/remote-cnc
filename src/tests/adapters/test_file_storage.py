"""Tests for FileSystemStorage adapter."""

import shutil
import time
from pathlib import Path
from typing import BinaryIO

import pytest
from core.adapters.file_storage import FileSystemStorage


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("path/to/files/file.txt", True),
        ("path/to/files/file.gcode", True),
        ("path/to/files/file.nc", True),
        ("path/to/files/file.TXT", True),
        ("path/to/files/file.GCODE", True),
        ("path/to/files/file.NC", True),
        ("path/to/files/file.py", False),
        ("path/to/files/file", False),
        ("", False),
    ],
)
def test_is_valid_filename(file_name, expected):
    assert FileSystemStorage._is_valid_filename(file_name) == expected


def test_get_file_path():
    base_path = "path/to/gcode_files/"
    file_name = "file.txt"
    expected = Path("path/to/gcode_files/1/file.txt")
    storage = FileSystemStorage(base_path)
    assert storage.get_file_path(1, file_name) == expected


# ---------------------------------------------------------------------------
# save_file
# ---------------------------------------------------------------------------


def test_save_file(mocker):
    file = BinaryIO()
    file_name = "file.gcode"
    user_id = 1
    expected = Path("path/to/gcode_files/1/file.gcode")

    mock_create_dir = mocker.patch.object(Path, "mkdir")
    mocked_file_data = mocker.mock_open(read_data="G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60")
    mocker.patch("builtins.open", mocked_file_data)
    mock_copy_file = mocker.patch.object(shutil, "copyfileobj")

    storage = FileSystemStorage(base_path="path/to/gcode_files/")
    result = storage.save_file(user_id, file, file_name)

    assert result == expected
    assert mock_create_dir.call_count == 1
    assert mock_copy_file.call_count == 1


def test_save_file_with_invalid_name(mocker):
    file = BinaryIO()
    file_name = "file.invalid"
    user_id = 1

    mock_create_dir = mocker.patch.object(Path, "mkdir")
    mock_copy_file = mocker.patch.object(shutil, "copyfileobj")

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.save_file(user_id, file, file_name)
    assert "Invalid file format, must be one of: " in str(error.value)

    assert mock_create_dir.call_count == 0
    assert mock_copy_file.call_count == 0


def test_save_file_with_os_error(mocker):
    file = BinaryIO()
    file_name = "file.gcode"
    user_id = 1

    mocker.patch.object(shutil, "copyfileobj", side_effect=Exception("mocked error"))

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.save_file(user_id, file, file_name)
    assert "There was an error writing the file in the file system" in str(error.value)


# ---------------------------------------------------------------------------
# copy_file
# ---------------------------------------------------------------------------


def test_copy_file(mocker):
    original_path = "path/to/file.gcode"
    file_name = "file.gcode"
    user_id = 1
    expected = Path("path/to/gcode_files/1/file.gcode")

    mock_create_dir = mocker.patch.object(Path, "mkdir")
    mock_copy_file = mocker.patch.object(shutil, "copy")

    storage = FileSystemStorage(base_path="path/to/gcode_files/")
    result = storage.copy_file(user_id, original_path, file_name)

    assert result == expected
    assert mock_create_dir.call_count == 1
    assert mock_copy_file.call_count == 1


def test_copy_file_with_invalid_name(mocker):
    original_path = "path/to/file.gcode"
    file_name = "file.invalid"
    user_id = 1

    mock_create_dir = mocker.patch.object(Path, "mkdir")
    mock_copy_file = mocker.patch.object(shutil, "copy")

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.copy_file(user_id, original_path, file_name)
    assert "Invalid file format, must be one of: " in str(error.value)

    assert mock_create_dir.call_count == 0
    assert mock_copy_file.call_count == 0


def test_copy_file_with_os_error(mocker):
    original_path = "path/to/file.gcode"
    file_name = "file.gcode"
    user_id = 1

    mocker.patch.object(shutil, "copy", side_effect=Exception("mocked error"))

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.copy_file(user_id, original_path, file_name)
    assert "There was an error writing the file in the file system" in str(error.value)


# ---------------------------------------------------------------------------
# rename_file
# ---------------------------------------------------------------------------


def test_rename_file(mocker):
    file_name = "file_20220610-192900.gcode"
    new_file_name = "file-updated.gcode"
    user_id = 1
    expected = Path("path/to/gcode_files/1/file-updated.gcode")

    mocker.patch.object(time, "strftime", return_value="20230720-192900")
    mock_rename_file = mocker.patch.object(Path, "rename")

    storage = FileSystemStorage(base_path="path/to/gcode_files/")
    result = storage.rename_file(user_id, file_name, new_file_name)

    assert result == expected
    assert mock_rename_file.call_count == 1


def test_rename_file_with_invalid_name(mocker):
    file_name = "file_20220610-192900.gcode"
    new_file_name = "file-updated.invalid"
    user_id = 1

    mock_rename_file = mocker.patch.object(Path, "rename")

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.rename_file(user_id, file_name, new_file_name)
    assert "Invalid file format, must be one of: " in str(error.value)

    assert mock_rename_file.call_count == 0


def test_rename_file_with_os_error(mocker):
    file_name = "1/file_20220610-192900.gcode"
    new_file_name = "file-updated.gcode"
    user_id = 1

    mocker.patch.object(Path, "rename", side_effect=Exception("mocked error"))

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.rename_file(user_id, file_name, new_file_name)
    assert "There was an error renaming the file in the file system" in str(error.value)


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------


def test_delete_file(mocker):
    file_name = "file_20230720-192900.gcode"
    user_id = 1

    mock_remove_file = mocker.patch.object(Path, "unlink")

    storage = FileSystemStorage(base_path="path/to/gcode_files/")
    storage.delete_file(user_id, file_name)

    assert mock_remove_file.call_count == 1


def test_delete_file_with_os_error(mocker):
    mocker.patch.object(Path, "unlink", side_effect=Exception("mocked error"))

    with pytest.raises(Exception) as error:
        storage = FileSystemStorage(base_path="path/to/gcode_files/")
        storage.delete_file(1, "file_name")
    assert "There was an error removing the file from the file system" in str(error.value)
