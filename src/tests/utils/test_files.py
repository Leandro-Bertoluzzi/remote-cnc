from pathlib import Path
from unittest.mock import MagicMock

import pytest
from core.utilities.files import (
    changeFileExtension,
    createFileIfNotExists,
    getFileNameInFolder,
    getFilesInFolder,
)


def test_getFileNameInFolder():
    current = "path/to/files/current.py"
    searched = "searched.txt"
    expected = Path("path/to/files/searched.txt")
    assert getFileNameInFolder(current, searched) == expected


def test_getFilesInFolder(mocker):
    item_a = MagicMock()
    item_a.name = "file_a.gcode"
    item_b = MagicMock()
    item_b.name = "file_b.nc"
    mocker.patch.object(Path, "iterdir", return_value=iter([item_a, item_b]))

    result = getFilesInFolder("path/to/files/")

    assert result == ["file_a.gcode", "file_b.nc"]


@pytest.mark.parametrize(
    "file_path,new_extension,expected",
    [
        ("file.gcode", "txt", "file.txt"),
        ("path/to/file.nc", "gcode", str(Path("path/to/file.gcode"))),
        ("archive.tar.gz", "nc", str(Path("archive.tar.nc"))),
    ],
)
def test_changeFileExtension(file_path, new_extension, expected):
    assert changeFileExtension(file_path, new_extension) == expected


def test_createFileIfNotExists_creates_file(mocker):
    mocked_open = mocker.mock_open()
    mocker.patch("builtins.open", mocked_open)

    createFileIfNotExists("path/to/new_file.gcode")

    mocked_open.assert_called_once_with("path/to/new_file.gcode", "x")


def test_createFileIfNotExists_does_not_raise_when_file_exists(mocker):
    mocker.patch("builtins.open", side_effect=FileExistsError)

    # Should not raise
    createFileIfNotExists("path/to/existing_file.gcode")
