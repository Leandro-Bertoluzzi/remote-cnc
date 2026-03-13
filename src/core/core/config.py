from dotenv import load_dotenv
import os

# Take environment variables from .env.
load_dotenv()

# DB connection
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME')
DB_HOST = os.environ.get('DB_HOST')

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB_CELERY = int(os.environ.get('REDIS_DB_CELERY', '0'))
REDIS_DB_STORAGE = int(os.environ.get('REDIS_DB_STORAGE', '1'))

# GRBL
GRBL_SIMULATION = bool(os.environ.get('GRBL_SIMULATION', ''))

# Serial communication
SERIAL_PORT = os.environ.get('SERIAL_PORT', '')
SERIAL_BAUDRATE = int(os.environ.get('SERIAL_BAUDRATE'))

# Security
TOKEN_SECRET = os.environ.get('TOKEN_SECRET', '')

# Files management
FILES_FOLDER_PATH = os.environ.get('FILES_FOLDER_PATH', '/app/gcode_files')
IMAGES_FOLDER_PATH = os.environ.get('IMAGES_FOLDER_PATH', '/app/thumbnails')
LOGS_FOLDER_PATH = os.environ.get('LOGS_FOLDER_PATH', '/app/logs')

# Generate global constants
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
CELERY_BROKER_URL = CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}'
