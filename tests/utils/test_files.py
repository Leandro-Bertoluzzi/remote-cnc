from utils.files import getFileNameInFolder

def test_getFileNameInFolder():
    current = "path\\to\\files\\current.py"
    searched = "searched.txt"
    expected = "path\\to\\files\\searched.txt"
    assert getFileNameInFolder(current, searched) == expected
