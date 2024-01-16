from pathlib import Path
import pytest
import shutil
import time
from typing import BinaryIO
from utils.files import isAllowedFile, getFileNameInFolder, computeSHA256, \
    computeSHA256FromFile, saveFile, copyFile, renameFile, deleteFile


@pytest.mark.parametrize(
        'file_name,expected',
        [
            ('path/to/files/file.txt', True),
            ('path/to/files/file.gcode', True),
            ('path/to/files/file.nc', True),
            ('path/to/files/file.TXT', True),
            ('path/to/files/file.GCODE', True),
            ('path/to/files/file.NC', True),
            ('path/to/files/file.py', False),
            ('path/to/files/file', False),
            ('', False)
        ]
    )
def test_isAllowedFile(file_name, expected):
    assert isAllowedFile(file_name) == expected


def test_getFileNameInFolder():
    current = 'path/to/files/current.py'
    searched = 'searched.txt'
    expected = Path('path/to/files/searched.txt')
    assert getFileNameInFolder(current, searched) == expected


def test_computeSHA256FromFile(mocker):
    expected_hash = '987d1fbbfe0da6111b6214ab798984bd96f45554c2c896bce758152045120937'

    # Mock FS methods
    mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Call method under test
    with open('/path/to/file') as test_file:
        computed_hash = computeSHA256FromFile(test_file)

    # Assertions
    assert computed_hash == expected_hash


def test_computeSHA256(mocker):
    file_name = 'path/to/file.gcode'
    expected_hash = '987d1fbbfe0da6111b6214ab798984bd96f45554c2c896bce758152045120937'

    # Mock FS methods
    mocked_file_data = mocker.mock_open(read_data=b'G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Assertions
    assert computeSHA256(file_name) == expected_hash


@pytest.mark.parametrize('user_folder_exists', [True, False])
def test_saveFile(mocker, user_folder_exists):
    file = BinaryIO()
    file_name = 'file.gcode'
    user_id = 1
    expected = Path('files_folder/1/file.gcode')

    # Mock folder creation
    mocker.patch.object(Path, 'is_dir', return_value=user_folder_exists)
    mock_create_dir = mocker.patch.object(Path, 'mkdir')
    create_dir_call_count = 0 if user_folder_exists else 1

    # Mock file copy
    mock_copy_file = mocker.patch.object(shutil, 'copyfileobj')

    # Call the method under test
    result = saveFile(user_id, file, file_name)

    # Assertions
    assert result == expected
    assert mock_create_dir.call_count == create_dir_call_count
    assert mock_copy_file.call_count == 1


def test_saveFile_with_invalid_name(mocker):
    file = BinaryIO()
    file_name = 'file.invalid'
    user_id = 1

    # Mock folder creation
    mock_create_dir = mocker.patch.object(Path, 'mkdir')

    # Mock file copy
    mock_copy_file = mocker.patch.object(shutil, 'copyfileobj')

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        saveFile(user_id, file, file_name)
    assert 'Invalid file format, must be one of: ' in str(error.value)

    # Assertions
    assert mock_create_dir.call_count == 0
    assert mock_copy_file.call_count == 0


def test_saveFile_with_os_error(mocker):
    file = BinaryIO()
    file_name = 'file.gcode'
    user_id = 1

    # Mock file copy and simulate exception
    mocker.patch.object(shutil, 'copyfileobj', side_effect=Exception('mocked error'))

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        saveFile(user_id, file, file_name)
    assert 'There was an error writing the file in the file system' in str(error.value)


@pytest.mark.parametrize('user_folder_exists', [True, False])
def test_copyFile(mocker, user_folder_exists):
    original_path = 'path/to/file.gcode'
    file_name = 'file.gcode'
    user_id = 1
    expected = Path('files_folder/1/file.gcode')

    # Mock folder creation
    mocker.patch.object(Path, 'is_dir', return_value=user_folder_exists)
    mock_create_dir = mocker.patch.object(Path, 'mkdir')
    create_dir_call_count = 0 if user_folder_exists else 1

    # Mock file copy
    mock_copy_file = mocker.patch.object(shutil, 'copy')

    # Call the method under test
    result = copyFile(user_id, original_path, file_name)

    # Assertions
    assert result == expected
    assert mock_create_dir.call_count == create_dir_call_count
    assert mock_copy_file.call_count == 1


def test_copyFile_with_invalid_name(mocker):
    original_path = 'path/to/file.gcode'
    file_name = 'file.invalid'
    user_id = 1

    # Mock folder creation
    mock_create_dir = mocker.patch.object(Path, 'mkdir')

    # Mock file copy
    mock_copy_file = mocker.patch.object(shutil, 'copy')

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        copyFile(user_id, original_path, file_name)
    assert 'Invalid file format, must be one of: ' in str(error.value)

    # Assertions
    assert mock_create_dir.call_count == 0
    assert mock_copy_file.call_count == 0


def test_copyFile_with_os_error(mocker):
    original_path = 'path/to/file.gcode'
    file_name = 'file.gcode'
    user_id = 1

    # Mock file copy and simulate exception
    mocker.patch.object(shutil, 'copy', side_effect=Exception('mocked error'))

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        copyFile(user_id, original_path, file_name)
    assert 'There was an error writing the file in the file system' in str(error.value)


def test_renameFile(mocker):
    # Set variables
    file_name = 'file_20220610-192900.gcode'
    new_file_name = 'file-updated.gcode'
    user_id = 1
    expected = Path('files_folder/1/file-updated.gcode')

    # Mock file update
    mocker.patch.object(time, 'strftime', return_value='20230720-192900')

    # Mock file update
    mock_rename_file = mocker.patch.object(Path, 'rename')

    # Call the method under test
    result = renameFile(user_id, file_name, new_file_name)

    # Assertions
    assert result == expected
    assert mock_rename_file.call_count == 1


def test_renameFile_with_invalid_name(mocker):
    file_name = 'file_20220610-192900.gcode'
    new_file_name = 'file-updated.invalid'
    user_id = 1

    # Mock file update
    mock_rename_file = mocker.patch.object(Path, 'rename')

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        renameFile(user_id, file_name, new_file_name)
    assert 'Invalid file format, must be one of: ' in str(error.value)

    # Assertions
    assert mock_rename_file.call_count == 0


def test_renameFile_with_os_error(mocker):
    file_name = '1/file_20220610-192900.gcode'
    new_file_name = 'file-updated.gcode'
    user_id = 1

    # Mock file update and simulate exception
    mocker.patch.object(Path, 'rename', side_effect=Exception('mocked error'))

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        renameFile(user_id, file_name, new_file_name)
    assert 'There was an error renaming the file in the file system' in str(error.value)


def test_deleteFile(mocker):
    file_name = 'file_20230720-192900.gcode'
    user_id = 1

    # Mock file removal
    mock_remove_file = mocker.patch.object(Path, 'unlink')

    # Assertions
    deleteFile(user_id, file_name)
    assert mock_remove_file.call_count == 1


def test_deleteFile_with_os_error(mocker):
    # Mock file removal and simulate exception
    mocker.patch.object(Path, 'unlink', side_effect=Exception('mocked error'))

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        deleteFile(1, 'file_name')
    assert 'There was an error removing the file from the file system' in str(error.value)
