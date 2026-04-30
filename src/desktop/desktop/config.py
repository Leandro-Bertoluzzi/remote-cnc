import os
from pathlib import Path

from desktop.helpers.configManager import ConfigManager

# Generate global constants
CONFIG_FILE = Path(__file__).parent / "config.ini"

# Initiate confiuration manager
appConfig = ConfigManager(CONFIG_FILE)
appConfig.load_config()

# Get user-defined variables
USER_ID = appConfig.get_int("general", "userid", 0)
SERIAL_PORT = appConfig.get_str("serial", "port", "")
SERIAL_BAUDRATE = appConfig.get_int("serial", "baudrate", 115200)

# Define constants
FILES_FOLDER_PATH = Path(__file__).parents[3] / "gcode_files"
IMAGES_FOLDER_PATH = Path(__file__).parents[3] / "thumbnails"
LOGS_FOLDER_PATH = Path(__file__).parents[3] / "logs"

# Set environment variables
os.environ["USER_ID"] = str(USER_ID)
os.environ["SERIAL_PORT"] = SERIAL_PORT
os.environ["SERIAL_BAUDRATE"] = str(SERIAL_BAUDRATE)
os.environ["FILES_FOLDER_PATH"] = str(FILES_FOLDER_PATH)
os.environ["IMAGES_FOLDER_PATH"] = str(IMAGES_FOLDER_PATH)
os.environ["LOGS_FOLDER_PATH"] = str(LOGS_FOLDER_PATH)
