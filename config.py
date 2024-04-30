from dotenv import load_dotenv
import os
from pathlib import Path

# Take environment variables from .env.
load_dotenv(override=True)

# Get environment variables
USER_ID = int(os.environ.get('USER_ID') or '0')
SERIAL_PORT = os.environ.get('SERIAL_PORT', '')
SERIAL_BAUDRATE = int(os.environ.get('SERIAL_BAUDRATE', ''))

# Generate global constants
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = '/app'   # If worker runs inside container
GRBL_LOGS_FILE = Path.cwd() / Path('core', 'logs', 'grbl.log')


# Utility functions
def suppressQtWarnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
