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

# Global state management
class Globals:
    current_task_id = 'abc-123'

    @classmethod
    def set_current_task_id(cls, id: str):
        cls.current_task_id = id

    @classmethod
    def get_current_task_id(cls) -> str:
        return cls.current_task_id
