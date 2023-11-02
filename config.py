from dotenv import load_dotenv
import os

# Take environment variables from .env.
load_dotenv()

# Get environment variables
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')
DB_HOST = os.environ.get('DB_HOST')
USER_ID = int(os.environ.get('USER_ID'))
FILES_FOLDER_PATH = './' + os.environ.get('FILES_FOLDER')
CELERY_BROKER_URL = './' + os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
SERIAL_PORT = os.environ.get('SERIAL_PORT')
SERIAL_BAUDRATE = os.environ.get('SERIAL_BAUDRATE')

# Generate global constants
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Utility functions
def suppressQtWarnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

# Global state management
class Globals:
    current_task_id = 0

    @classmethod
    def set_current_task_id(cls, id):
        cls.current_task_id = id

    @classmethod
    def get_current_task_id(cls):
        return cls.current_task_id
