import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any
from urllib.parse import urlparse

from data.postgres_provider import PostgresDataProvider
from services.ollama_service import OllamaService
from services.search_service import SearchService
from services.url_validation_service import UrlValidationService
from utils.config import config

logger = logging.getLogger(__name__)
_discovery_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="external-discovery")


class ExternalCourseService:
    def __init__(self):
        self.postgres = PostgresDataProvider()
        self.ollama = OllamaService()
        self.search = SearchService()
        self.validator = UrlValidationService()

    def discover_courses(self, weak_topics: list[str], force_refresh: bool = False) -> dict[str, Any]:
        if not config.WEB_SEARCH_ENABLED:
            return {"saved": 0, "queries": [], "results": []}

        resources = self.discover_resources(weak_topics)
        selected = self._select_persistable_resources(resources)
        saved = self.postgres.upsert_external_courses([self._to_db_course(resource) for resource in selected])
        return {
            "saved": saved,
            "queries": list(dict.fromkeys([item.get("SearchQuery", "") for item in resources if item.get("SearchQuery")])),
            "results": selected,
        }

    def discover_resources(self, weak_topics: list[str]) -> list[dict[str, Any]]:
        if not config.WEB_SEARCH_ENABLED:
            return []

        queries = self.ollama.generate_search_queries(weak_topics) if config.OLLAMA_EXTERNAL_SEARCH_ENABLED else []
        if not queries:
            queries = self._build_resource_queries(weak_topics)

        discovered: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for query in queries:
            try:
                results = self.search.search(
                    query,
                    max_results=config.WEB_SEARCH_MAX_RESULTS,
                    allowed_domains=config.EXTERNAL_RESOURCE_DOMAINS,
                )
            except Exception as ex:
                logger.warning("Search failed for query '%s': %s", query, ex)
                continue

            for item in results:
                candidate = self._build_validated_candidate(query, item)
                if not candidate:
                    continue
                url = candidate.get("Url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                discovered.append(candidate)

        return discovered

    def discover_fresh_candidates(self, topics: list[str], timeout_seconds: int | None = None) -> list[dict[str, Any]]:
        clean_topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        if not clean_topics:
            return []
        future = _discovery_executor.submit(self.discover_resources, clean_topics)
        try:
            return future.result(timeout=timeout_seconds or config.FRESH_DISCOVERY_TIMEOUT_SECONDS)
        except TimeoutError:
            logger.info("Fresh external discovery timed out after %s seconds", timeout_seconds or config.FRESH_DISCOVERY_TIMEOUT_SECONDS)
            return []
        except Exception as ex:
            logger.warning("Fresh external discovery failed: %s", ex)
            return []

    def persist_resources(self, resources: list[dict[str, Any]]) -> int:
        selected = self._select_persistable_resources(resources)
        return self.postgres.upsert_external_courses([self._to_db_course(resource) for resource in selected])

    def discover_courses_background(self, weak_topics: list[str], force_refresh: bool = False) -> None:
        if not config.WEB_SEARCH_ENABLED or not config.EXTERNAL_DISCOVERY_BACKGROUND_ENABLED:
            return
        topics = [str(topic).strip() for topic in weak_topics if str(topic).strip()]
        if not topics:
            return

        def _run() -> None:
            try:
                result = self.discover_courses(topics, force_refresh=force_refresh)
                logger.info(
                    "Background external discovery finished: topics=%s saved=%s queries=%s",
                    topics,
                    result.get("saved", 0),
                    result.get("queries", []),
                )
            except Exception as ex:
                logger.warning("Background external discovery failed for topics %s: %s", topics, ex)

        _discovery_executor.submit(_run)

    def _build_resource_queries(self, weak_topics: list[str], max_queries: int = 3) -> list[str]:
        queries = []
        for topic in weak_topics[:max_queries]:
            topic_text = str(topic).strip()
            if not topic_text:
                continue
            queries.extend([
                f'site:coursera.org/learn "{topic_text}" course',
                f'site:edx.org/learn "{topic_text}" course',
                f'site:youtube.com/watch "{topic_text}" tutorial',
                f'site:learn.microsoft.com "{topic_text}" tutorial',
                f'site:developer.mozilla.org "{topic_text}" tutorial',
                f'site:geeksforgeeks.org "{topic_text}" tutorial',
                f'site:w3schools.com "{topic_text}" tutorial',
                f'site:coursera.org/specializations "{topic_text}" course',
            ])
        return queries

    def _build_validated_candidate(self, query: str, item: dict) -> dict[str, Any] | None:
        raw_url = item.get("url")
        resource_type = self.validator.detect_resource_type(raw_url)
        validation = self.validator.validate(raw_url, expected_type=resource_type)
        if not validation.is_valid:
            if resource_type != "video" and self._is_trusted_resource_domain(raw_url) and not self.validator.title_looks_like_error(item.get("title")):
                logger.info("Accept trusted search result without direct fetch validation: %s", raw_url)
                normalized_url = self.validator.normalize_url(raw_url)
                validation.normalized_url = normalized_url
            else:
                logger.info("Skip invalid external resource %s: %s", raw_url, validation.reason)
                try:
                    self.postgres.deactivate_external_course(validation.normalized_url or raw_url)
                except Exception:
                    pass
                return None

        url = validation.normalized_url or raw_url
        if self.validator.title_looks_like_error(item.get("title")):
            return None

        page: dict[str, Any] = {"url": url}
        if resource_type != "video":
            try:
                page = self.search.extract_course_page(url)
            except Exception as ex:
                logger.info("Page extraction skipped for %s: %s", url, ex)

        return self._normalize_without_ollama(query, item, page, resource_type)

    def _normalize_without_ollama(self, query: str, item: dict, page: dict, resource_type: str | None = None) -> dict:
        url = page.get("url") or item.get("url") or ""
        title = page.get("title") or item.get("title") or "External course"
        description = (
            page.get("description")
            or item.get("content")
            or item.get("description")
            or "External course found by NeuroTutor search."
        )
        resource_type = resource_type or self.validator.detect_resource_type(url)
        confidence = self._confidence_for_url(url, resource_type)
        return {
            "Title": str(title)[:300],
            "Description": str(description)[:1000],
            "Platform": self._detect_platform(url),
            "Difficulty": "Standard",
            "Topics": [str(topic) for topic in query.replace('"', "").split()[:8] if not topic.startswith("site:")],
            "Url": url,
            "ResourceType": resource_type,
            "RelevanceScore": confidence,
            "Language": "en",
            "ProviderCourseId": None,
            "ConfidenceScore": confidence,
            "Metadata": {"source": "searxng_fallback", "search_result": item},
            "SearchQuery": query,
            "DiscoveryMethod": "searxng_fallback",
        }

    def _select_persistable_resources(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        courses = [
            item for item in resources
            if item.get("ResourceType") == "course" and self._is_course_domain(item.get("Url"))
        ]
        has_specific_by_query: set[str] = {
            item.get("SearchQuery", "")
            for item in courses
            if self.validator.is_specific_course_url(item.get("Url"))
        }
        selected = []
        for item in courses:
            if item.get("SearchQuery") in has_specific_by_query and not self.validator.is_specific_course_url(item.get("Url")):
                continue
            selected.append(item)

        for item in resources:
            if item.get("ResourceType") in {"article", "video"} and self._is_trusted_resource_domain(item.get("Url")):
                selected.append(item)

        deduped: dict[str, dict[str, Any]] = {}
        for item in selected:
            url = self.validator.normalize_url(item.get("Url"))
            if not url:
                continue
            if url not in deduped or item.get("ConfidenceScore", 0) > deduped[url].get("ConfidenceScore", 0):
                deduped[url] = item
        return list(deduped.values())

    def _to_db_course(self, item: dict[str, Any]) -> dict:
        return {
            "title": item.get("Title", ""),
            "description": item.get("Description", ""),
            "platform": item.get("Platform", "External"),
            "difficulty": item.get("Difficulty", "Standard"),
            "topics": item.get("Topics") or [],
            "url": item.get("Url"),
            "language": item.get("Language", "en"),
            "provider_course_id": item.get("ProviderCourseId"),
            "resource_type": item.get("ResourceType", "course"),
            "confidence_score": item.get("ConfidenceScore", 0.0),
            "metadata": item.get("Metadata", {}),
            "search_query": item.get("SearchQuery", ""),
            "discovery_method": item.get("DiscoveryMethod", "searxng_fallback"),
        }

    def _confidence_for_url(self, url: str, resource_type: str) -> float:
        if resource_type == "video":
            return 0.72
        if self.validator.is_specific_course_url(url):
            return 0.85
        if "/courses" in urlparse(url).path.lower():
            return 0.42
        if resource_type == "article":
            return 0.65
        return 0.5

    @staticmethod
    def _is_course_domain(url: str | None) -> bool:
        host = urlparse(url or "").netloc.lower()
        return any(domain in host for domain in config.TRUSTED_COURSE_DOMAINS)

    @staticmethod
    def _is_trusted_resource_domain(url: str | None) -> bool:
        host = urlparse(url or "").netloc.lower()
        return any(domain in host for domain in config.EXTERNAL_RESOURCE_DOMAINS)

    @staticmethod
    def _detect_platform(url: str) -> str:
        lower = url.lower()
        if "coursera" in lower:
            return "Coursera"
        if "edx" in lower:
            return "edX"
        if "youtube" in lower or "youtu.be" in lower:
            return "YouTube"
        if "learn.microsoft.com" in lower:
            return "Microsoft Learn"
        if "developer.mozilla.org" in lower:
            return "MDN"
        return "External"
