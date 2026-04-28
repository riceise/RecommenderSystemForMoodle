import os
from dotenv import load_dotenv

load_dotenv()

def _int_env(name: str, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(min_value, min(value, max_value))

class Config:
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    MOODLE_API_URL = os.getenv('MOODLE_API_URL', 'https://your-moodle-instance.com')
    MOODLE_API_TOKEN = os.getenv('MOODLE_API_TOKEN')

    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:9b')

    WEB_SEARCH_ENABLED = os.getenv('WEB_SEARCH_ENABLED', 'true').lower() == 'true'
    SEARXNG_BASE_URL = os.getenv('SEARXNG_BASE_URL', 'http://localhost:8080')
    WEB_SEARCH_MAX_RESULTS = _int_env('WEB_SEARCH_MAX_RESULTS', 5, 1, 10)
    WEB_SEARCH_TIMEOUT_SECONDS = _int_env('WEB_SEARCH_TIMEOUT_SECONDS', 8, 1, 15)
    COURSE_PAGE_TIMEOUT_SECONDS = _int_env('COURSE_PAGE_TIMEOUT_SECONDS', 8, 1, 15)
    URL_VALIDATION_TIMEOUT_SECONDS = _int_env('URL_VALIDATION_TIMEOUT_SECONDS', 5, 1, 10)
    FRESH_DISCOVERY_TIMEOUT_SECONDS = _int_env('FRESH_DISCOVERY_TIMEOUT_SECONDS', 18, 3, 30)
    WEB_SEARCH_RESULTS_PER_TOPIC = _int_env('WEB_SEARCH_RESULTS_PER_TOPIC', 5, 1, 8)
    EXTERNAL_SEARCH_CACHE_TTL_HOURS = _int_env('EXTERNAL_SEARCH_CACHE_TTL_HOURS', 24, 1, 168)
    EXTERNAL_SEARCH_DOMAINS = [
        item.strip() for item in os.getenv('EXTERNAL_SEARCH_DOMAINS', 'coursera.org,edx.org').split(',') if item.strip()
    ]
    EXTERNAL_RESOURCE_DOMAINS = [
        item.strip()
        for item in os.getenv(
            'EXTERNAL_RESOURCE_DOMAINS',
            'coursera.org,edx.org,learn.microsoft.com,developer.mozilla.org,geeksforgeeks.org,w3schools.com,youtube.com,www.youtube.com,youtu.be'
        ).split(',')
        if item.strip()
    ]
    TRUSTED_COURSE_DOMAINS = [
        item.strip()
        for item in os.getenv('TRUSTED_COURSE_DOMAINS', 'coursera.org,edx.org').split(',')
        if item.strip()
    ]
    OLLAMA_GENERATE_TIMEOUT_SECONDS = _int_env('OLLAMA_GENERATE_TIMEOUT_SECONDS', 20, 1, 30)
    OLLAMA_QUERY_TIMEOUT_SECONDS = _int_env('OLLAMA_QUERY_TIMEOUT_SECONDS', 8, 1, 15)
    OLLAMA_NORMALIZE_TIMEOUT_SECONDS = _int_env('OLLAMA_NORMALIZE_TIMEOUT_SECONDS', 8, 1, 15)
    OLLAMA_HEALTH_TIMEOUT_SECONDS = _int_env('OLLAMA_HEALTH_TIMEOUT_SECONDS', 5, 1, 10)
    OLLAMA_EXTERNAL_SEARCH_ENABLED = os.getenv('OLLAMA_EXTERNAL_SEARCH_ENABLED', 'false').lower() == 'true'
    EXTERNAL_DISCOVERY_BACKGROUND_ENABLED = os.getenv('EXTERNAL_DISCOVERY_BACKGROUND_ENABLED', 'true').lower() == 'true'

    LIGHTFM_EPOCHS = 20
    LIGHTFM_COMPONENTS = 30

    DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')

config = Config()
