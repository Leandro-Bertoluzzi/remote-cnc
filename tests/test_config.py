import os
from config import suppressQtWarnings

def test_suppressQtWarnings():
    # Check environment variables before
    assert os.getenv("QT_DEVICE_PIXEL_RATIO") == "auto"
    assert os.getenv("QT_AUTO_SCREEN_SCALE_FACTOR") is None
    assert os.getenv("QT_SCREEN_SCALE_FACTORS") is None
    assert os.getenv("QT_SCALE_FACTOR") is None

    # Call the function under test
    suppressQtWarnings()

    # Check if environment variables are set correctly
    assert os.getenv("QT_DEVICE_PIXEL_RATIO") == "0"
    assert os.getenv("QT_AUTO_SCREEN_SCALE_FACTOR") == "1"
    assert os.getenv("QT_SCREEN_SCALE_FACTORS") == "1"
    assert os.getenv("QT_SCALE_FACTOR") == "1"
