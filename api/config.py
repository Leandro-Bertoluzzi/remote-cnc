from dotenv import load_dotenv
import os
from pathlib import Path

# Take environment variables from .env.
load_dotenv()

# Get environment variables
SERIAL_PORT = os.environ.get('SERIAL_PORT', '')
SERIAL_BAUDRATE = int(os.environ.get('SERIAL_BAUDRATE'))
TOKEN_SECRET = os.environ.get('TOKEN_SECRET', '')
FILES_FOLDER_PATH = os.environ.get('FILES_FOLDER_PATH', '/app/gcode_files')
