import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    MOODLE_API_URL = os.getenv('MOODLE_API_URL', 'https://your-moodle-instance.com')
    MOODLE_API_TOKEN = os.getenv('MOODLE_API_TOKEN')

    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:9b')

    WEB_SEARCH_ENABLED = os.getenv('WEB_SEARCH_ENABLED', 'true').lower() == 'true'
    SEARXNG_BASE_URL = os.getenv('SEARXNG_BASE_URL', 'http://localhost:8080')
    WEB_SEARCH_MAX_RESULTS = int(os.getenv('WEB_SEARCH_MAX_RESULTS', '5'))
    EXTERNAL_SEARCH_CACHE_TTL_HOURS = int(os.getenv('EXTERNAL_SEARCH_CACHE_TTL_HOURS', '24'))
    EXTERNAL_SEARCH_DOMAINS = [
        item.strip() for item in os.getenv('EXTERNAL_SEARCH_DOMAINS', 'coursera.org,edx.org').split(',') if item.strip()
    ]

    LIGHTFM_EPOCHS = 20
    LIGHTFM_COMPONENTS = 30

    DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')

config = Config()