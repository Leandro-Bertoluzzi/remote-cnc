from helpers.configManager import ConfigManager
import os
from pathlib import Path

# Generate global constants
GRBL_LOGS_FILE = Path.cwd().parent / Path('core', 'logs', 'grbl.log')
CONFIG_FILE = Path.cwd() / 'config.ini'

# Initiate confiuration manager
appConfig = ConfigManager(CONFIG_FILE)
appConfig.load_config()

# Get user-defined variables
USER_ID = appConfig.get_int('general', 'userid', 0)
FILES_FOLDER_PATH = appConfig.get_str('general', 'gcodefiles')
SERIAL_PORT = appConfig.get_str('serial', 'port', '')
SERIAL_BAUDRATE = appConfig.get_int('serial', 'baudrate', 115200)


# Utility functions
def suppressQtWarnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
