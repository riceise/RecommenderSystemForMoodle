import json
import logging
from typing import Any

import requests

from utils.config import config

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL.rstrip('/')
        self.model = config.OLLAMA_MODEL

    def generate_json(self, system_prompt: str, user_prompt: str) -> Any:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "format": "json",
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("message", {}).get("content", "{}").strip()
        return json.loads(content)

    def generate_search_queries(self, weak_topics: list[str], max_queries: int = 3) -> list[str]:
        if not weak_topics:
            return []

        system_prompt = (
            "Ты генерируешь поисковые запросы для поиска онлайн-курсов. "
            "Верни только JSON {\"queries\": [...]} без лишнего текста."
        )
        user_prompt = json.dumps(
            {
                "weak_topics": weak_topics,
                "domains": config.EXTERNAL_SEARCH_DOMAINS,
                "max_queries": max_queries,
                "goal": "find online courses relevant to weak topics on Coursera and edX",
            },
            ensure_ascii=False,
        )

        try:
            result = self.generate_json(system_prompt, user_prompt)
            queries = result.get("queries", []) if isinstance(result, dict) else []
            return [str(q).strip() for q in queries if str(q).strip()][:max_queries]
        except Exception as ex:
            logger.warning("Failed to generate search queries with Ollama: %s", ex)
            return [f'site:{config.EXTERNAL_SEARCH_DOMAINS[0]} "{topic}" course' for topic in weak_topics[:max_queries]]

    def normalize_course(self, raw_course: dict) -> dict | None:
        system_prompt = (
            "Ты нормализуешь карточку онлайн-курса. "
            "Верни только JSON с ключами: title, description, platform, difficulty, topics, url, language, provider_course_id, confidence_score, is_valid_course, metadata."
        )
        user_prompt = json.dumps(raw_course, ensure_ascii=False)
        try:
            result = self.generate_json(system_prompt, user_prompt)
            if not isinstance(result, dict) or not result.get("is_valid_course", True):
                return None
            return result
        except Exception as ex:
            logger.warning("Failed to normalize course with Ollama: %s", ex)
            return None