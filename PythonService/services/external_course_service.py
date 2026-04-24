import logging
from typing import Any

from data.postgres_provider import PostgresDataProvider
from services.ollama_service import OllamaService
from services.search_service import SearchService
from utils.config import config

logger = logging.getLogger(__name__)


class ExternalCourseService:
    def __init__(self):
        self.postgres = PostgresDataProvider()
        self.ollama = OllamaService()
        self.search = SearchService()

    def discover_courses(self, weak_topics: list[str], force_refresh: bool = False) -> dict[str, Any]:
        if not config.WEB_SEARCH_ENABLED:
            return {"saved": 0, "queries": [], "results": []}

        queries = self.ollama.generate_search_queries(weak_topics)
        discovered: list[dict] = []
        seen_urls: set[str] = set()

        for query in queries:
            try:
                results = self.search.search(query)
            except Exception as ex:
                logger.warning("Search failed for query '%s': %s", query, ex)
                continue

            for item in results:
                url = item.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                try:
                    page = self.search.extract_course_page(url)
                    normalized = self.ollama.normalize_course({
                        "query": query,
                        "search_result": item,
                        "page": page,
                    })
                    if not normalized:
                        continue
                    normalized["url"] = normalized.get("url") or url
                    normalized["search_query"] = query
                    normalized["discovery_method"] = "ollama_search"
                    normalized.setdefault("platform", self._detect_platform(url))
                    discovered.append(normalized)
                except Exception as ex:
                    logger.warning("Failed to parse/normalize url '%s': %s", url, ex)

        saved = self.postgres.upsert_external_courses(discovered)
        return {
            "saved": saved,
            "queries": queries,
            "results": discovered,
        }

    @staticmethod
    def _detect_platform(url: str) -> str:
        lower = url.lower()
        if "coursera" in lower:
            return "Coursera"
        if "edx" in lower:
            return "edX"
        return "External"