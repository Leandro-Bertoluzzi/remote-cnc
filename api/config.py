from dotenv import load_dotenv
import os
from pathlib import Path

# Take environment variables from .env.
load_dotenv()

# Get environment variables
SERIAL_PORT = os.environ.get('SERIAL_PORT', '')
SERIAL_BAUDRATE = int(os.environ.get('SERIAL_BAUDRATE'))
TOKEN_SECRET = os.environ.get('TOKEN_SECRET', '')

# Generate global constants
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = '/app'   # If worker runs inside container
GRBL_LOGS_FILE = Path.cwd() / Path('core', 'logs', 'grbl.log')
