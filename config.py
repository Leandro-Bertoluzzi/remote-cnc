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
FILES_FOLDER_PATH = './' + os.environ.get('FILES_FOLDER', '')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', ''))
REDIS_DB_CELERY = int(os.environ.get('REDIS_DB_CELERY', ''))
REDIS_DB_STORAGE = int(os.environ.get('REDIS_DB_STORAGE', ''))

# Generate global constants
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
CELERY_BROKER_URL = CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}'
