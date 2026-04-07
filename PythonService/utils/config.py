import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    MOODLE_API_URL = os.getenv('MOODLE_API_URL', 'https://your-moodle-instance.com')
    MOODLE_API_TOKEN = os.getenv('MOODLE_API_TOKEN')

    LIGHTFM_EPOCHS = 20
    LIGHTFM_COMPONENTS = 30

    DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')

config = Config()