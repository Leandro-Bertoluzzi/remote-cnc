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
FILES_FOLDER_PATH = './' + os.environ.get('FILES_FOLDER')
CELERY_BROKER_URL = './' + os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
SERIAL_PORT = os.environ.get('SERIAL_PORT')
SERIAL_BAUDRATE = os.environ.get('SERIAL_BAUDRATE')

# Generate global constants
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
