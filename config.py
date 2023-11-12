from dotenv import load_dotenv
import os

# Take environment variables from .env.
load_dotenv()

# Get environment variables
USER_ID = int(os.environ.get('USER_ID'))

# Utility functions
def suppressQtWarnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

# Global state management
class Globals:
    current_task_id = 'abc-123'

    @classmethod
    def set_current_task_id(cls, id: str):
        cls.current_task_id = id

    @classmethod
    def get_current_task_id(cls) -> str:
        return cls.current_task_id
